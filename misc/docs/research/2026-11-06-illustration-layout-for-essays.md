# Illustration layout for essays: placement and size across the GitHub review comment, Substack and Medium

Research date: 2026-11-06. Scope: rules penult can apply when it places and sizes illustrations in an essay draft, first in the GitHub issue comment used for review, then in the Substack draft built by `article` through python-substack, and, for completeness, in a Medium import. Tags: **[S]** = stated by a cited source or measured in this research; **[J]** = my judgment, derived from the sources but not stated by any of them.

## Summary and recommendation

**Why the hero looked huge.** A 1024x1024 image rendered with plain `![]()` in a GitHub issue comment is scaled to the full comment width, about 878 px on a wide desktop, so it is drawn 878 px tall, which is taller than the visible part of most laptop screens [S: measured, 19, 31]. On Substack the same image at column width is 728x728 px [S: measured, 13]. Nielsen Norman Group names large hero graphics that push content below the fold as a cause of the "illusion of completeness" and advises against full-screen hero content [S, 6]; users "dislike huge photos that get in the way" [S, 5]. The problem is the square aspect ratio at full measure, not the presence of a hero.

**Rules penult can apply.**

1. **Size vocabulary.** Use four size classes in the source, mapped per renderer: `inset`, `normal`, `large`, `full`. The vocabulary mirrors what the platforms already have: Substack's editor offers column width (default), "Set large size" and "Toggle full width", and its stylesheet has `sizing-normal`, `sizing-large`, `sizing-fullscreen` [S, 11, 12, 13]; the Guardian's renderer has `supporting` (300-380 px, beside the text), `inline` (620 px, the column), `showcase` (780-860 px, wider than the column) and `immersive` (full width) [S, 7]; Tufte CSS has margin, main-column and full-width figures [S, 2]; Medium has several placements from inset to full width [S, 10, 25]. Default class is `normal` [J].
2. **Hero (opening image).** Place it directly under the title and subtitle, before the first paragraph [S for the convention: 10; Substack uses the first image as the default social preview: 16]. Make it landscape, 16:9 or 3:2; python-substack's default image box is 1456x819 (16:9) [S, 14], and Wikipedia sizes wide images up and tall ones down [S, 3]. Render it at full column width (`normal`) only when it is landscape; a 16:9 hero at 728 px is about 410 px tall, which leaves the opening paragraph visible on a laptop [J]. **Cap the rendered height of any hero at about 420 px** (roughly half of a laptop viewport) [J, from 6]. A square hero should be rendered as an `inset` at 400-420 px wide, or regenerated or cropped to landscape; prefer generating heroes at 16:9 in the first place [J].
3. **Inset (supporting illustration, square or portrait).** Render at 50-60% of the column: **about 400 px wide** on GitHub (`<img width="400">`) and `resizeWidth` 364-440 on Substack's 728 px column [J; the Guardian's supporting role is 300-380 px [S, 7]; Wikipedia's default thumbnail is 250 px, with exceptions "no more than 400px wide and 500px tall" [S, 3]]. Portrait images: also cap rendered height at about 500 px [S for the 500 px cap on Wikipedia, 3; J for applying it here].
4. **Diagram, chart, table-as-image.** Full column width (`normal`); use `large` only when the detail cannot be read at column width, and know that Substack's large size renders on the web only, not in email [S, 12]. Supply the file at least 1456 px wide, which is 2x Substack's 728 px column (Substack stores body images at 1456 px wide) and above Medium's 1192 px minimum for all placement options [S: measured 13; 25].
5. **`full` is opt-in.** Never default to full width in an essay; it suits an image that is itself the content (a map, a panorama) [S: freeCodeCamp's Medium guide reserves full-bleed for images "chock full of interesting data", 10; J].
6. **Frequency.** For an essay, at most one illustration per 500-1000 words after the hero, and only where the image has its own purpose; zero body images is acceptable [J]. Sourced bounds: Wikipedia says "less is more" and each image needs "a clear and unique illustrative purpose" [S, 3]; NN/g found decorative images are ignored while informative ones are scrutinised [S, 5]. The often-quoted "an image every 75-100 words" comes from a social-share correlation in marketing content, which BuzzSumo itself says is not meant literally; do not use it for essays [S, 9].
7. **Placement.** Put a body image immediately after the paragraph that first refers to it, never before it and never at the end of the previous section [S, 3, 2].
8. **Captions.** One line, a sentence fragment without a final period unless it contains a full sentence; say what the image means for the argument, not what it depicts in detail; at most about three lines [S, 4]. Do not italicise the caption in the source: Wikipedia says not to unless the text would be italic anyway, Medium does not support italic captions, and Substack renders captions upright, centred, 15 px, grey [S, 4, 25, 13]. In the GitHub comment, mimic the platform: render the caption under the image, small and centred (for example `<p align="center"><sub>caption</sub></p>`), not as an italic paragraph [J, from 19]. Credits: keep them out of the caption unless relevant [S, 4]; for generated or third-party images, put the credit at the end of the caption in a short form when a licence or disclosure requires it [J].
9. **Alt text always.** Every image gets alt text describing its content; it is a separate field on Substack (`alt` attr) and Medium [S, 14, 25].
10. **How to carry size from source to renderers.** Keep `![alt](src "caption")` as the only image syntax in the Markdown that `article` sends to python-substack, and carry the size class out of band: either a front-matter map `{image file -> size class}` or python-substack's own `<!-- python-substack-image:v1 <base64 JSON> -->` marker placed right after the image line, which merges attrs such as `imageSize` and `resizeWidth` into the `image2` node [S: verified in python-substack 0.10.0 source and by test, 14]. Do **not** put `{width=...}` or `<img width>` into the Markdown that goes to python-substack: the first turns the image into a paragraph of alt text, the second drops the image entirely [S: tested, 14]. penult's GitHub renderer, which writes its own comment, should emit `<img src alt width>` (GitHub keeps `width`, `height`, `alt`, `title`, `align`) [S: tested through GitHub's Markdown API, 19].

**Concrete mapping penult can use** [J, built on the measurements above]:

| class | GitHub comment | Substack `image2` attrs | email |
|---|---|---|---|
| `inset` | `<img width="400">`, centred | `imageSize: "normal"`, `resizeWidth: 400` | scaled into the ~600 px email body |
| `normal` (default) | `<img width="100%">` or no width, landscape only | `imageSize: "normal"`, `resizeWidth: 728` (python-substack default) | full email width |
| `large` | same as `normal` (the comment is already 878 px) | `imageSize: "large"` (inferred value, verify) | renders as normal; large is web-only |
| `full` | same as `normal` | `fullscreen: true` (verify) | renders as normal (assumed) |

Always also set `width`/`height` to the real pixel size of the file (article already does this for uploaded images, after its issue 8) so the box has the right aspect ratio [S: 14 and article's own code].

## 1. Editorial and typographic practice

**Measure.** Butterick recommends 45-90 characters per line and calls neglected line length the main flaw of responsive layouts [S, 1]. All three platforms enforce a measure of roughly 680-880 px: Substack 728 px, Medium 680 px, GitHub issue comment up to about 878 px [S: measured, 13, 31, 19]. Images are sized relative to this column, so a rule stated as a fraction of the column (50-60% inset, 100% normal) transfers across platforms better than a pixel value [J].

**Size tiers.** Every mature long-form system I checked has the same three or four tiers. Tufte CSS: margin figures, main-column figures (the default, "constrained to the main column"), and full-width figures [S, 2]. The Guardian's article renderer: `thumbnail` 120-140 px, `supporting` 300-380 px floated beside text on desktop, `inline` 620 px (the column), `showcase` 780-860 px, `immersive` up to 1900 px, plus `halfWidth` [S, 7]. Wikipedia: default thumbnail 250 px scaled by an `upright` factor, `upright=1.6` "the largest value for images floated beside text", lead images at most `upright=1.2` or 300 px [S, 3]. Medium: several placements from a small inset to full width; a Medium style guide says "Most of the time, you'll want to stick with column width" and to avoid the side-straddle size because it makes text less comfortable to read [S, 10, 25].

**When full measure is right.** For the opening image and for images whose detail is the content (charts, diagrams, maps) [S, 10; 2]. A smaller inset suits portraits, objects, and illustrations whose role is to set a mood rather than to inform [J]. NN/g's eyetracking found that users scrutinise images that carry information and ignore "purely decorative images", and that they "dislike huge photos that get in the way of their tasks" [S, 5]. That argues for keeping decorative illustrations, which most generated woodcuts are, at inset size in the body [J].

**Aspect ratios in one column.** Landscape fits a single column best because its rendered height stays small: at 728 px, 16:9 is 410 px tall, 3:2 is 485 px, 1:1 is 728 px, 2:3 is 1092 px [J, arithmetic]. Wikipedia advises that short, wide images use `upright` 1 or more and tall, narrow ones 1 or less, which is the same rule stated as width [S, 3]. python-substack's default image box is 1456x819 (16:9) [S, 14].

**Hero placement and the fold.** NN/g lists "large hero graphics or videos" as a cause of the illusion of completeness and recommends avoiding full-screen hero content so that further content "peeks" above the fold [S, 6]. A Medium style guide recommends "a high-resolution image at the top of a story under your headline" [S, 10]. Substack takes the first image of a post as the default social preview and marks it `topImage: true` in the post JSON [S, 16; measured, 13].

**Frequency.** No editorial source I found gives a words-per-image rate for essays. Wikipedia: "usually, less is more" and "prioritize quality over quantity" [S, 3]. The BuzzSumo figure (articles with an image every 75-100 words got about twice the shares) is a correlation in social sharing of marketing content, and BuzzSumo's own write-up says it "isn't quite that literal" [S, 9]. Early Poynter/Stanford eyetracking of online news found readers went to text before photos, unlike print readers [S, secondary, 32]. Hence the judgment rule above (one per 500-1000 words, each with a purpose) [J].

**Placement relative to the text.** Tufte: introduce a figure "directly into the main flow of discussion" [S, 2]. Wikipedia: put images in the most relevant section, not too early, and not at the end of the previous section because it may land in the wrong place on mobile [S, 3].

**Captions and credits.** Wikipedia's caption guideline: a caption identifies the subject, says why the image is there and draws the reader into the text; succinct; over about three lines is distracting; fragments take no final period unless the caption contains a full sentence; no italics unless the text would be italic in running prose; credits belong on the file page, not in the article, unless relevant [S, 4]. Captions are well read: an eyetracking study of a 300-word article (95 usable participants) found "91% read the image caption" [S, 8]. Bringhurst: I could not access the text of The Elements of Typographic Style in this session, so no claim here rests on it.

## 2. Substack specifics

**Column width.** The post body (`.body.markup`) measured 728 px on a 1525-1678 px desktop viewport, on two different publications [S: measured, 13]. A third-party importer hard-codes the same value (`const SUBSTACK_WIDTH = 728`) [S, 15]; a third-party FAQ says 730 px [S, 16]. On mobile the column is the viewport minus small gutters; Substack's `sizing-large` rule uses `max-width: calc(100vw - 30px)`, which suggests 15 px gutters [S: stylesheet, 13; J for the inference].

**Editor size options.** Substack announced "Toggle full width" (full width vs column width) in January 2022 [S, 11] and "Set large size" (beyond the column, not full screen, web only, not in email) plus drag-to-resize from the lower-right corner in February 2022 [S, 12]. Substack's current stylesheet contains `img.sizing-large`, `img.sizing-fullscreen`, `.image2-full-screen` and also `.image2-align-left`, `.image2-align-right`, `.image2-offset-left`, `.image2-offset-right`; live posts carry `class="sizing-normal"` [S: measured, 13]. A news report says Substack was testing images beside text with wrapping, described as work in progress [S, 17]; python-substack 0.10.0 already lists `align` and `offset` among `image2` attrs [S, 14].

**`imageSize` values.** Not documented by Substack. Observed: `"normal"` (python-substack's default) and `null` on images in a Substack-authored post [S, 14, 13]. Inferred from the CSS class names: `"large"` for "Set large size"; full width is the separate boolean `fullscreen` attr, rendered as `image2-full-screen` [J, from 13]. I found no Substack or python-substack document confirming `"large"` or any other value; verify by setting the size in the editor on a test draft and reading the draft JSON back.

**`resizeWidth`.** Set by drag-resizing; it is the displayed width in px within the 728 px column. Leaflet's Substack importer treats `resizeWidth < 728` as a user-chosen reduced width and scales it proportionally [S, 15]. python-substack's `captioned_image` sets `resizeWidth: 728` when `imageSize == "normal"`, `null` otherwise [S, 14]. Images in Substack's own post had `resizeWidth: null` [S, 13]. That Substack's renderer honours a smaller `resizeWidth` written through the API is likely but not verified [J].

**How a square renders.** At `normal` with no resize, a 1:1 image fills the column: 728x728 on desktop [J, from measured column width and the behaviour of all `sizing-normal` images observed, 13].

**Stored size.** Images in Substack's post data are capped at 1456 px wide (2x the column): 1462x908 and 1466x642 sources were stored as 1456 px wide [S: measured, 13].

**Cover / social image vs first body image.** By default the first image in the post is the social preview; it can be replaced in post settings [S, 16]. Recommended preview size is reported as at least 1456x1048 (about 1.39:1) by a third-party FAQ, with a warning that the ratio crops; other sites give 1200x630 [S, weak, 16]. I found no official Substack help page confirming either figure.

**Captions and alt text.** Captions render as `figcaption.image-caption`: serif, 15 px, centred, grey, upright (not italic) [S: measured, 13]. Alt text is a separate attr (`alt`), set in the editor from the image menu [S, 12, 14]. python-substack maps Markdown alt to `alt` and the Markdown title to the caption node [S, 14].

**Email.** "Large" renders on the web only, not in email [S, 12]. I could not find Substack's email body width; the convention across email builders is about 600 px, because wider messages can produce scrollbars in some clients [S, 18]. Treat any image wider than the email body as scaled down to it [J].

**python-substack issues/docs about image attrs.** The README documents images, linked images and captions from Markdown, and lossless preservation of unsupported widgets through `python-substack-node:v1` markers [S, 14]. The 0.10.0 source also has `python-substack-image:v1|v2` markers: an HTML comment right after an image, holding base64 JSON attrs, merged into the preceding `image2` node; `v1` refuses `src`, `alt`, `href`, `isProcessing` [S: source and test, 14]. That marker is the cleanest seam for penult to set `imageSize`/`resizeWidth` without changing python-substack [J].

## 3. GitHub Markdown in issue comments

All claims in this section were checked by rendering a test document through GitHub's Markdown API (`POST /markdown`, `mode: gfm`) on 2026-11-06 [19], which uses the same rendering pipeline as comments [J: the API is documented as rendering GFM, 19; comment rendering may add client-side behaviour].

- **`![]()` images** get `style="max-width: 100%;"` and no width, so they scale to the comment width when the file is wider [S: tested, 19]. Measured comment body width: 878 px in the issue view at a 1280 px layout container (wide desktop); 738-814 px on a pull-request timeline [S: measured, 31]. On a phone the width is the viewport minus margins (not measured) [J].
- **`<img>` attributes kept:** `src` (proxied through camo), `width` (pixels or percent, e.g. `width="60%"`), `height`, `alt`, `title`, `align`. GitHub rewrites `style`: with width and height it sets `max-width: 100%; height: auto; max-height: <height>px; aspect-ratio: w / h`. Author `style` and `class` are removed [S: tested, 19]. The open-source html-pipeline allowlist agrees: `width`, `height`, `align`, `alt`, `title` are allowed on all elements [S, 21].
- **`<p align="center">` / `<div align="center">`:** kept [S: tested, 19, 21].
- **`<figure>` / `<figcaption>`:** stripped on github.com, leaving the image and the caption text as loose inline text [S: tested, 19], although the open-source html-pipeline allowlist includes both [S, 21]. Production differs from the open-source filter here; do not use them.
- **`<picture>` with `<source media="(prefers-color-scheme: dark)">`:** kept, wrapped in a `themed-picture` element [S: tested, 19]; documented as supported [S, 20, 24]. The `#gh-dark-mode-only` / `#gh-light-mode-only` URL fragments are kept in the URL and applied by GitHub's CSS [S: tested, 19; 23].
- **`<details>` / `<summary>`:** kept [S: tested, 19]. Useful for collapsing the image block or a long caption in a review comment [J].
- **`<sub>`:** kept [S, 20; tested, 19]; a good caption style.
- **GFM tag filter:** GFM additionally disallows a fixed list of raw tags (`title`, `textarea`, `style`, `xmp`, `iframe`, `noembed`, `noframes`, `script`, `plaintext`) [S, 22].

## 4. Medium import (for completeness)

Medium's column measured 680 px wide, with figures at 680 px and captions 14 px, centred [S: measured, 31]. Medium's editor offers several image placements once an image is at least 1192 px wide, puts captions beneath the image, and does not support italics in captions [S, 25]. The "Import a story" tool fetches a published URL, backdates the post and adds a canonical link [S, 26]; the help page says nothing about image sizes, so imported images should be expected to arrive at the default column width, with any inset or full-width choice re-applied in Medium's editor [J]. Source files at 1456 px wide (rule 4) clear the 1192 px threshold [J].

## 5. A portable way to express per-image size

| convention | where it comes from | GitHub (GFM) | markdown-it-py `commonmark` (python-substack, article) | markdown-it-py + `attrs_plugin` |
|---|---|---|---|---|
| `![a](x.png){width=60%}` | pandoc `link_attributes` [27]; markdown-it-attrs (JS) [30] | literal `{width=60%}` text after the image [S: tested, 19] | literal text; python-substack then turns the whole paragraph into alt text, losing the image [S: tested, 14] | unquoted `%` not parsed; `{width="60%"}`, `{width=400}`, `{.large}` all parsed into attributes [S: tested, 28] |
| `![a](x.png =400x)` | markdown-it-imsize style; markdown-it-image-size reads real file sizes instead [29] | broken: link text, no image [S: tested, 19] | not an image [S: tested] | not an image [S: tested] |
| `![a\|400](x.png)` | Obsidian | image with alt `a\|400` [J] | image with alt `a\|400` [S: tested] | same [S: tested] |
| `<img src width>` | HTML | kept [S: tested, 19] | HTML block; python-substack drops it (no image in the draft) [S: tested, 14] | same |
| HTML comment after the image | python-substack image marker [14] | invisible | merged into `image2` attrs by python-substack [S: tested, 14] | same |
| front-matter map `images: {file: size}` | Jekyll/Hugo-style convention [J] | invisible (front matter is not in the comment) | ignored by the parser | ignored |
| size class (`inset`/`normal`/`large`/`full`) | Substack, Guardian, Tufte tiers [11, 12, 7, 2] | needs mapping to `width` | needs mapping to attrs | `{.inset}` parses to `class` [S: tested] |

**Recommendation** [J]: keep the essay source as plain CommonMark images `![alt](file "caption")` so every renderer sees a valid image, and record the size class out of band, in penult's own front matter or manifest (`{image: class}`), the SSOT. Each renderer maps the class: penult's GitHub-comment renderer emits `<img width>` plus a `<sub>` caption; `article` emits the python-substack image marker (or sets attrs in its post-processing step, where it already sets `width`/`height`). If an inline syntax is wanted later, `{.inset}` with markdown-it-py's `attrs_plugin` is the least surprising (pandoc and markdown-it-attrs read it too), but it must be stripped before the Markdown reaches python-substack.

## REFERENCES

1. [Butterick, M. Line length. Practical Typography.](https://practicaltypography.com/line-length.html)
2. [Liepmann, D. Tufte CSS (figures, margin figures, full-width figures).](https://edwardtufte.github.io/tufte-css/)
3. [Wikipedia: Manual of Style/Images.](https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Images)
4. [Wikipedia: Manual of Style/Captions.](https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Captions)
5. [Nielsen, J. Photos as Web Content (Not All Images Are the Same). Nielsen Norman Group, 2010, reviewed 2026.](https://www.nngroup.com/articles/photos-as-web-content/)
6. [Flaherty, K. The Illusion of Completeness: What It Is and How to Avoid It. Nielsen Norman Group, 2016.](https://www.nngroup.com/articles/illusion-of-completeness/)
7. [The Guardian, frontend repository: ContentWidths.scala (image roles and widths by breakpoint).](https://github.com/guardian/frontend/blob/1c10341994ff5a73aa5f94ea120f1878956ee600/common/app/layout/ContentWidths.scala)
8. [Speero. How People Read Short Articles (eye-tracking study).](https://speero.com/post/how-people-read-short-articles-original-research)
9. [BuzzSumo. How to massively boost your blog traffic with these 5 awesome image stats.](https://buzzsumo.com/blog/how-to-massively-boost-your-blog-traffic-with-these-5-awesome-image-stats/)
10. [Larson, Q. A style guide for writing on Medium. freeCodeCamp.](https://www.freecodecamp.org/news/a-style-guide-for-writing-on-medium-fcbad27492ea)
11. [Substack. New tools for writers: Image and layout options, version history, more. 2022-01-10.](https://on.substack.com/p/new-tools-layout-options)
12. [Substack. Product news for writers: Fresh tools, updates, and fixes. 2022-02-18.](https://on.substack.com/p/product-news-tools-updates)
13. [Measurement for this report (2026-11-06): DOM, `data-attrs` and stylesheet of a Substack post, read in a desktop browser.](https://on.substack.com/p/new-tools-layout-options)
14. [ma2za/python-substack v0.10.0 source: substack/nodes.py, substack/mdrender.py, substack/mdexport.py, README (read and exercised locally for this report).](https://github.com/ma2za/python-substack/tree/v0.10.0/substack)
15. [Leaflet. Substack importer, substackToBlocks.ts.](https://tangled.org/leaflet.pub/leaflet/blob/main/src/substackImport/substackToBlocks.ts)
16. [Substack Image Size FAQ: The Definitive Guide (third-party publication).](https://frequentlyaskedquestions.substack.com/p/substack-image-size-faq-the-definitive)
17. [RuntimeWire. Substack tests text wrapping after years of writer requests.](https://runtimewire.com/article/substack-tests-image-text-wrapping)
18. [GetResponse Help. How wide should my message be?](https://www.getresponse.com/help/how-wide-should-my-message-be.html)
19. [GitHub Docs. REST API endpoints for Markdown (`POST /markdown`, used here to render the test document on 2026-11-06).](https://docs.github.com/en/rest/markdown/markdown)
20. [GitHub Docs. Basic writing and formatting syntax.](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
21. [gjtorikian/html-pipeline. sanitization_filter.rb (default allowlist).](https://github.com/gjtorikian/html-pipeline/blob/main/lib/html_pipeline/sanitization_filter.rb)
22. [GitHub Flavored Markdown Spec. Disallowed Raw HTML (extension).](https://github.github.com/gfm/#disallowed-raw-html-extension-)
23. [GitHub Changelog. Specify theme context for images in Markdown. 2021-11-24.](https://github.blog/changelog/2021-11-24-specify-theme-context-for-images-in-markdown/)
24. [GitHub Changelog. Specify theme context for images in Markdown (GA). 2022-08-15.](https://github.blog/changelog/2022-08-15-specify-theme-context-for-images-in-markdown-ga)
25. [Medium Help Center. Using images.](https://help.medium.com/hc/en-us/articles/215679797-Images)
26. [Medium Help Center. Importing a post to Medium.](https://help.medium.com/hc/en-us/articles/214550207-Import-post)
27. [Pandoc User's Guide. Extension: link_attributes.](https://pandoc.org/MANUAL.html#extension-link_attributes)
28. [mdit-py-plugins documentation. Attributes (`attrs_plugin`).](https://mdit-py-plugins.readthedocs.io/en/latest/#attributes)
29. [markdown-it-image-size (npm).](https://www.npmjs.com/package/markdown-it-image-size)
30. [arve0/markdown-it-attrs.](https://github.com/arve0/markdown-it-attrs)
31. [Measurement for this report (2026-11-06): `.markdown-body` width on a GitHub issue page (and a pull-request timeline), and article column and figure widths on a Medium post.](https://github.com/microsoft/vscode/issues/100) Medium page measured: [Tips and Tricks for Medium Writers](https://medium.com/blog/tips-and-tricks-for-medium-writers-1d79498101c3).
32. [Editor & Publisher. Online news readers prefer text over graphics (on the Stanford/Poynter EyeTrack study).](https://www.editorandpublisher.com/stories/online-news-readers-prefer-text-over-graphics,19526)
