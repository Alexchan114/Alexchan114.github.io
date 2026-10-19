# Article pinning / 文章置顶

The site is built with Hugo. Published pages are generated from `site-src`.

网站使用 Hugo，从 `site-src` 生成发布页面。

To pin an article, set this Boolean in its front matter:

在文章开头的元数据中设置：

```yaml
pinned: true
```

Set the same value in the Chinese `.md` and English `.en.md` translations. Set `pinned: false`, or remove the field from both files, to unpin. Rebuild and publish the site for the change to appear.

中文 `.md` 与英文 `.en.md` 文件需同步设置。取消置顶时，两份文件均改为 `pinned: false` 或移除该字段，再重新构建并发布网站。

Pinned articles appear first in page lists with a localized “置顶 / Pinned” label. Multiple pinned articles are ordered by date, newest first. Other articles retain descending date order. Pinning does not change the article date or URL.

置顶文章排在列表前面，并显示“置顶 / Pinned”。多篇置顶文章之间按日期从新到旧排序，其余文章保持日期倒序。置顶不改变发布日期或文章链接。
