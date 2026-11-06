"""Tavotto source: actual partition membership and unaltered native screenshots."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / 'partition.json').read_text(encoding='utf-8'))
INK, TEAL, RUST, PAPER = '#233b49', '#117f7d', '#b75a36', '#faf9f5'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK,
                     'axes.labelcolor': INK, 'pdf.fonttype': 42, 'savefig.facecolor': 'white'})


def heading(fig, number, title, subtitle):
    fig.text(.045, .95, number + ' / ' + title, fontsize=16, weight='bold', color=INK)
    fig.text(.045, .91, subtitle, fontsize=9, color='#657780')


fig = plt.figure(figsize=(10, 5.5))
ax = fig.add_axes([.01, .15, .98, .70], projection='3d')
faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
for element, conn in P['elements'].items():
    xyz = np.array([P['nodes'][str(n)] for n in conn])
    color = TEAL if int(element) in P['sub_elements'] else RUST
    ax.add_collection3d(Poly3DCollection([xyz[list(face)] for face in faces], facecolors=color,
        edgecolors='#233b4970', linewidths=.5, alpha=.36))
interface = np.array([P['nodes'][str(n)] for n in P['interface_nodes']])
root = np.array([P['nodes'][str(n)] for n in P['root_nodes']])
ax.scatter(*interface.T, s=26, c='#ebbd48', edgecolors=INK, depthshade=False)
ax.scatter(*root.T, s=22, c=INK, depthshade=False)
ax.set(xlim=(0, 12), ylim=(0, 2), zlim=(0, 2), xlabel='x / mm', ylabel='y / mm', zlabel='z / mm')
ax.set_xticks([0, 3, 6, 9, 12])
ax.set_yticks([])
ax.set_zticks([])
ax.set_ylabel('')
ax.set_zlabel('')
ax.set_box_aspect((12, 2, 2))
ax.view_init(elev=21, azim=-64)
ax.grid(False)
heading(fig, '07', 'THE PARTITION IS A SET OF ACTUAL IDS', 'Same recorded 6 mm cut in both native attempts; geometry is parsed from the existing INP.')
fig.legend(handles=[Patch(facecolor=TEAL, label='SUB / 24 C3D8'), Patch(facecolor=RUST, label='CORE / 24 C3D8'),
    Patch(facecolor='#ebbd48', label='Interface / 9 nodes'), Patch(facecolor=INK, label='Root / 9 nodes')],
    loc='lower center', bbox_to_anchor=(.5, .08), ncol=4, frameon=False, fontsize=9)
fig.text(.05, .035, 'Section 2 x 2 mm | 18 retained nodes | 45 internal nodes x 3 = 135 eliminated DOFs | no SUB stress recovery', fontsize=9)
fig.savefig(ROOT / 'partition.pdf')
plt.close(fig)

labels = [('full_reference', 'A / INDEPENDENT FULL REFERENCE', 'All 48 solid elements; host calibration evidence.'),
          ('claude_reduced', 'B / CLAUDE CODE REDUCED RESULT', '24 retained solid elements; SUB internal stress unavailable.'),
          ('codex_late_reduced', 'C / CODEX LATE HOST SUPPLEMENT', 'Completed after the agent deadline. Original grade unchanged.')]
for kind, field, subtitle in [('stress', 'MISES STRESS / MPa', 'Stored S tensor; scalar-before-average; section regions; Avg75. Each panel retains its own native legend.'),
                              ('deformation', 'DISPLACEMENT / mm', 'Stored U magnitude; deformation scale 1. Each panel retains its own native legend.')]:
    fig = plt.figure(figsize=(10, 10))
    heading(fig, '08' if kind == 'stress' else '09', field + ' FROM THE EXISTING ODB', subtitle)
    for i, (label, title, caption) in enumerate(labels):
        top = .86 - i * .278
        fig.text(.045, top, title, fontsize=11, weight='bold', color=RUST if i == 2 else INK)
        ax = fig.add_axes([.035, top - .218, .93, .205])
        ax.imshow(plt.imread(ROOT / 'raw' / label / (kind + '.png')))
        ax.axis('off')
        fig.text(.045, top - .238, caption, fontsize=9, color='#657780')
    fig.text(.045, .025, 'Pull / frame 20 / time 1 | original public mm-N-MPa model | read-only postprocessing | no new solve', fontsize=9)
    fig.savefig(ROOT / (kind + '.pdf'))
    plt.close(fig)
