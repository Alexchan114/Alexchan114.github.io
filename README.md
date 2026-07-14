# AlexanderChan Technical Blog

个人技术博客，基于 [Hugo XMin](https://github.com/yihui/hugo-xmin)（MIT）改造并发布到 GitHub Pages。

- Hugo 内容管理与文章归档
- 深灰强调色和纯色背景
- 研究笔记、项目档案、标签与 RSS
- 响应式阅读布局

## Source

Hugo 源文件位于 `site-src/`，生成后的静态站点发布在仓库根目录。

## Build

```powershell
.\.tools\hugo-0.164.0\hugo.exe --source "$PWD\site-src" --destination "$PWD\site-dist"
```

网站地址：<https://alexchan114.github.io/>
