"""Executed by the installed pvpython, not the MCP Python interpreter."""
import json
import math
from pathlib import Path
import sys
import traceback
from paraview import simple as pv


def inspect(proxy):
    info = proxy.GetDataInformation()
    result = {'points': info.GetNumberOfPoints(), 'cells': info.GetNumberOfCells(), 'bounds': list(info.GetBounds()), 'arrays': {}}
    for name, data in (('POINTS', info.GetPointDataInformation()), ('CELLS', info.GetCellDataInformation())):
        arrays = []
        for i in range(data.GetNumberOfArrays()):
            array = data.GetArrayInformation(i)
            n = array.GetNumberOfComponents()
            item = {'name': array.GetName(), 'components': n,
                    'ranges': [[float(x) if math.isfinite(x) else None for x in array.GetComponentRange(c)] for c in range(n)]}
            if n > 1:
                item['tuple_magnitude_range'] = [float(x) if math.isfinite(x) else None for x in array.GetComponentRange(-1)]
            arrays.append(item)
        result['arrays'][name] = arrays
    return result


def main(request, work):
    args, op = request['arguments'], request['operation']
    if op == 'pv_run_script':
        source = Path(args['script_path'])
        sys.argv = [str(source)] + args.get('arguments', [])
        exec(compile(source.read_text(encoding='utf-8-sig'), str(source), 'exec'), {'__name__': '__main__', '__file__': str(source)})
        return {'script_completed': True}
    source = pv.OpenDataFile(args['data_path'])
    if source is None:
        raise ValueError('No ParaView reader could open the input')
    source.UpdatePipelineInformation()
    times = list(getattr(source, 'TimestepValues', []))
    frame = args.get('frame', -1)
    if times:
        index = len(times)-1 if frame == -1 else frame
        if index >= len(times):
            raise ValueError('Frame index exceeds available timesteps')
        time = times[index]
        source.UpdatePipeline(time=time)
    else:
        if frame not in (-1, 0):
            raise ValueError('Input is static; only frame 0/last is valid')
        index, time = 0, None
        source.UpdatePipeline()
    metadata = inspect(source)
    metadata.update(frame_index=index, timestep=time, available_timesteps=times)
    if op == 'pv_inspect':
        return metadata
    if op == 'pv_render':
        association = args['association']
        available = metadata['arrays'][association]
        chosen = args['array_name']
        if chosen == 'auto':
            choices = [a['name'] for a in available if a['name'].startswith('S_MISES') and not a['name'].endswith(('_VariationPct', '_Averaged'))]
            chosen = choices[0] if choices else 'U' if any(a['name']=='U' for a in available) else 'none'
        array = next((a for a in available if a['name']==chosen), None)
        if chosen != 'none' and array is None:
            raise ValueError('Selected color array does not exist in '+association+': '+chosen)
        if array and args['component'] >= array['components']:
            raise ValueError('Color component out of range')
        display_source = source
        if args['deformation_scale']:
            if not any(a['name']=='U' and a['components']==3 for a in metadata['arrays']['POINTS']):
                raise ValueError('Deformation requires three-component point U')
            display_source = pv.WarpByVector(Input=source)
            display_source.Vectors = ['POINTS', 'U']
            display_source.ScaleFactor = args['deformation_scale']
            display_source.UpdatePipeline(time=time) if time is not None else display_source.UpdatePipeline()
        view = pv.CreateView('RenderView')
        if time is not None:
            view.ViewTime = time
        view.ViewSize = [args['width'], args['height']]
        view.Background = [0.96, 0.97, 0.99]
        view.UseColorPaletteForBackground = 0
        representation = pv.Show(display_source, view)
        representation.Representation = args['representation']
        if chosen != 'none':
            pv.ColorBy(representation, (association, chosen))
            lut = pv.GetColorTransferFunction(chosen)
            lut.VectorMode = 'Component' if args['component'] >= 0 else 'Magnitude'
            if args['component'] >= 0:
                lut.VectorComponent = args['component']
            representation.RescaleTransferFunctionToDataRange(True, False)
            # Showing a new representation can initially fetch timestep zero.
            # Bind the legend to the inspected requested frame explicitly.
            selected_range = (array['ranges'][args['component']] if args['component'] >= 0
                              else array.get('tuple_magnitude_range', array['ranges'][0]))
            if all(x is not None for x in selected_range):
                lut.RescaleTransferFunction(*selected_range)
            representation.SetScalarBarVisibility(view, True)
            bar = pv.GetScalarBar(lut, view)
            if args.get('scalar_label'):
                bar.Title = args['scalar_label']
                bar.ComponentTitle = ''
        bounds = metadata['bounds']
        center = [(bounds[2*i]+bounds[2*i+1])/2 for i in range(3)]
        length = max(bounds[2*i+1]-bounds[2*i] for i in range(3)) or 1
        offsets = {'isometric': [1.3, -1.1, 0.9], 'xy': [0, 0, 1], 'xz': [0, -1, 0], 'yz': [1, 0, 0]}
        orientation = args.get('view', 'isometric')
        view.CameraFocalPoint = center
        view.CenterOfRotation = center
        view.CameraPosition = [center[i]+length*offsets[orientation][i] for i in range(3)]
        view.CameraViewUp = [0, 1, 0] if orientation=='xy' else [0, 0, 1]
        view.CameraParallelProjection = 1
        view.ResetCamera()
        if time is not None:
            view.ViewTime = time
        pv.Render(view)
        output = work / 'preview.png'
        pv.SaveScreenshot(str(output), view, ImageResolution=[args['width'], args['height']])
        pv.SaveState(str(work / 'scene.pvsm'))
        color_range = [float(lut.RGBPoints[0]),float(lut.RGBPoints[-4])] if chosen != 'none' else None
        return {'image_path': str(output), 'state_path': str(work/'scene.pvsm'), 'color_array': chosen,
                'color_range':color_range,'rendered_timestep':float(view.ViewTime),
                'rendered_bounds':list(display_source.GetDataInformation().GetBounds()),
                'association': association, 'view': orientation, 'metadata': metadata}
    if op == 'pv_slice':
        filtered = pv.Slice(Input=source)
        filtered.SliceType = 'Plane'
        filtered.SliceType.Origin = args['origin']
        filtered.SliceType.Normal = args['normal']
        if 'MergePoints' in filtered.ListProperties():
            filtered.MergePoints = 0
        filtered.UpdatePipeline(time=time) if time is not None else filtered.UpdatePipeline()
        result = inspect(filtered)
        if result['cells'] == 0:
            raise ValueError('Slice plane does not intersect the selected data')
        output = work / 'slice.vtp'
        pv.SaveData(str(output), proxy=filtered)
        return {'data_path': str(output), 'metadata': result,
                'note': 'Use the original export for exact nodal averaging comparisons; downstream interpolation is a separate operation.'}
    if op == 'pv_line':
        filtered = pv.PlotOverLine(Input=source)
        filtered.Point1, filtered.Point2 = args['point1'], args['point2']
        if 'Resolution' in filtered.ListProperties():
            filtered.Resolution = args['resolution']
        filtered.UpdatePipeline(time=time) if time is not None else filtered.UpdatePipeline()
        output = work / 'line.csv'
        metadata = inspect(filtered)
        identifiers = {'NodeLabel', 'ElementLabel', 'InstanceId', 'AveragingRegionId', 'SectionAssignmentId'}
        excluded = [a['name'] for a in metadata['arrays']['POINTS'] if a['name'] in identifiers or a['name'].endswith(('_VariationPct','_Averaged'))]
        selected = [a['name'] for a in metadata['arrays']['POINTS'] if a['name'] not in excluded]
        pv.SaveData(str(output), proxy=filtered, ChooseArraysToWrite=1, PointDataArrays=selected, Precision=17)
        return {'csv_path': str(output), 'metadata': metadata, 'excluded_interpolated_diagnostics': excluded,
                'note': 'Respect vtkValidPointMask. Original IDs and averaging flags are excluded from CSV because interpolation does not preserve their meaning; no smoothing is applied.'}
    raise ValueError('Unknown ParaView operation')


if __name__ == '__main__':
    work = Path.cwd()
    try:
        request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        result = main(request, work)
        response = {'ok': True, 'result': result}
    except SystemExit as error:
        response = {'ok': True, 'result': {'script_completed': True}} if error.code in (None, 0) else {'ok': False, 'error': str(error)}
    except BaseException as error:
        response = {'ok': False, 'error': str(error), 'traceback': traceback.format_exc()}
    (work/'native_result.json').write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding='utf-8')
