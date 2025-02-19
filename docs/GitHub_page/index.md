---
layout: splash
title: "Batcher"
excerpt: "A batch image processing plug-in for GIMP."
custom_subtitle: "Batch image processing plug-in for GIMP"
header:
  overlay_image: /assets/images/splash.jpg
  actions:
    - label: "Download 1.0-RC3 (February 13, 2025)"
      image: <svg class="page__header-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M288 32c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 242.7-73.4-73.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l128 128c12.5 12.5 32.8 12.5 45.3 0l128-128c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L288 274.7 288 32zM64 352c-35.3 0-64 28.7-64 64l0 32c0 35.3 28.7 64 64 64l384 0c35.3 0 64-28.7 64-64l0-32c0-35.3-28.7-64-64-64l-101.5 0-45.3 45.3c-25 25-65.5 25-90.5 0L165.5 352 64 352zm368 56a24 24 0 1 1 0 48 24 24 0 1 1 0-48z"/></svg>
      url: "https://github.com/kamilburda/batcher/releases/download/1.0-RC3/batcher-1.0-RC3.zip"
  show_overlay_excerpt: true
feature_row_main:
  - title: "Batch Convert"
    image_path: "/assets/images/feature_batch_convert.svg"
    excerpt: "Loads image files and converts them to another file format. Supports any file format provided by GIMP and third-party plug-ins."
    url: "/docs/usage#batch-image-conversion"
    btn_label: "Read More"
    btn_class: "btn--primary"
  - title: "Export Layers"
    image_path: "/assets/images/feature_export_layers.svg"
    excerpt: "Exports each layer as separate images from an image opened in GIMP. Can also export group layers."
    url: "/docs/usage#exporting-layers"
    btn_label: "Read More"
    btn_class: "btn--primary"
  - title: "Edit Layers"
    image_path: "/assets/images/feature_edit_layers.svg"
    excerpt: "Applies edits to each layer individually in an image opened in GIMP, such as renaming or color adjustment."
    url: "/docs/usage#editing-layers"
    btn_label: "Read More"
    btn_class: "btn--primary"
feature_row_customization:
  - image_path: /assets/images/feature_procedures_and_constraints.png
    title: "Highly customizable, too."
    excerpt: "Apply any filter to each image/layer during batch processing, including third-party scripts and plug-ins. Process only images/layers that match the specified criteria."
    url: "/docs/customization/"
    btn_label: "Read More"
    btn_class: "btn--primary"
---

{% include feature_row id="feature_row_main" %}

{% include feature_row id="feature_row_customization" type="left" %}


## Support

Feel free to [ask questions](https://github.com/kamilburda/batcher/discussions) related to Batcher.

Found a bug? You can [report it on GitHub](https://github.com/kamilburda/batcher/issues). Just make sure to check the GitHub issues and the [known issues](docs/known-issues) first. Thank you. 😊
