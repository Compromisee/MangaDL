import os
import uuid
import zipfile
from io import BytesIO
from PIL import Image


class EPUBExporter:
    name = "EPUB"
    extension = ".epub"

    def export(self, title: str, chapter_name: str, image_paths: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_chapter = self._safe_name(chapter_name)
        os.makedirs(os.path.join(output_dir, safe_title), exist_ok=True)
        output_path = os.path.join(output_dir, safe_title, f"{safe_chapter}.epub")

        full_title = f"{title} - {chapter_name}"
        images = self._prepare_images(image_paths)
        self._write_epub(output_path, full_title, images)
        return output_path

    def export_volume(self, title: str, volume_name: str, chapters_data: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_vol = self._safe_name(volume_name)
        os.makedirs(os.path.join(output_dir, safe_title), exist_ok=True)
        output_path = os.path.join(output_dir, safe_title, f"{safe_vol}.epub")

        full_title = f"{title} - {volume_name}"
        all_images = []
        for ch_name, paths in chapters_data:
            for p in paths:
                all_images.append(p)

        images = self._prepare_images(all_images)
        self._write_epub(output_path, full_title, images)
        return output_path

    def _prepare_images(self, image_paths: list) -> list:
        """
        Convert all images to JPEG for maximum compatibility.
        Returns list of (jpeg_bytes, width, height).
        """
        results = []
        for path in image_paths:
            try:
                with Image.open(path) as img:
                    img = img.convert("RGB")
                    w, h = img.size
                    buf = BytesIO()
                    img.save(buf, format="JPEG", quality=92)
                    results.append((buf.getvalue(), w, h))
            except Exception:
                continue
        return results

    def _write_epub(self, output_path: str, title: str, images: list):
        """
        Write a valid EPUB 3 fixed-layout file from scratch.
        No dependencies on ebooklib — full manual construction.
        """
        book_uid = str(uuid.uuid4())

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. mimetype — MUST be first, stored uncompressed
            zf.writestr(
                zipfile.ZipInfo("mimetype", date_time=(2024, 1, 1, 0, 0, 0)),
                "application/epub+zip",
                compress_type=zipfile.ZIP_STORED,
            )

            # 2. META-INF/container.xml
            zf.writestr("META-INF/container.xml", self._container_xml())

            # 3. Add images
            manifest_items = []
            spine_items = []

            for i, (jpeg_data, w, h) in enumerate(images):
                idx = i + 1
                img_file = f"OEBPS/images/page_{idx:04d}.jpg"
                page_file = f"OEBPS/text/page_{idx:04d}.xhtml"
                img_id = f"img_{idx:04d}"
                page_id = f"page_{idx:04d}"

                # Write image
                zf.writestr(img_file, jpeg_data)

                # Write XHTML page
                xhtml = self._page_xhtml(idx, w, h)
                zf.writestr(page_file, xhtml)

                manifest_items.append(
                    f'    <item id="{img_id}" href="images/page_{idx:04d}.jpg" media-type="image/jpeg"/>'
                )
                manifest_items.append(
                    f'    <item id="{page_id}" href="text/page_{idx:04d}.xhtml" media-type="application/xhtml+xml"/>'
                )
                spine_items.append(
                    f'    <itemref idref="{page_id}"/>'
                )

            # 4. Write nav.xhtml
            nav_xhtml = self._nav_xhtml(title, len(images))
            zf.writestr("OEBPS/nav.xhtml", nav_xhtml)

            manifest_items.append(
                '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
            )

            # 5. Write content.opf
            opf = self._content_opf(book_uid, title, manifest_items, spine_items)
            zf.writestr("OEBPS/content.opf", opf)

    def _container_xml(self) -> str:
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''

    def _content_opf(self, uid: str, title: str, manifest_items: list, spine_items: list) -> str:
        manifest_str = "\n".join(manifest_items)
        spine_str = "\n".join(spine_items)
        safe_title = self._esc(title)

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:{uid}</dc:identifier>
    <dc:title>{safe_title}</dc:title>
    <dc:language>en</dc:language>
    <dc:creator>Unknown</dc:creator>
    <meta property="dcterms:modified">2024-01-01T00:00:00Z</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">none</meta>
  </metadata>
  <manifest>
{manifest_str}
  </manifest>
  <spine>
{spine_str}
  </spine>
</package>'''

    def _page_xhtml(self, page_num: int, width: int, height: int) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width={width}, height={height}"/>
  <title>Page {page_num}</title>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: {width}px;
      height: {height}px;
      overflow: hidden;
    }}
    body {{
      background: #000;
    }}
    img {{
      display: block;
      width: {width}px;
      height: {height}px;
      margin: 0;
      padding: 0;
      border: 0;
    }}
  </style>
</head>
<body>
  <img src="../images/page_{page_num:04d}.jpg" alt="Page {page_num}"/>
</body>
</html>'''

    def _nav_xhtml(self, title: str, page_count: int) -> str:
        safe_title = self._esc(title)
        li_items = []
        for i in range(1, page_count + 1):
            li_items.append(f'      <li><a href="text/page_{i:04d}.xhtml">Page {i}</a></li>')
        li_str = "\n".join(li_items)

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="UTF-8"/>
  <title>{safe_title}</title>
</head>
<body>
  <nav epub:type="toc">
    <h1>{safe_title}</h1>
    <ol>
{li_str}
    </ol>
  </nav>
</body>
</html>'''

    def _esc(self, text: str) -> str:
        return (
            (text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _safe_name(self, name: str) -> str:
        return "".join(c if c.isalnum() or c in " -_.()" else "_" for c in name).strip()