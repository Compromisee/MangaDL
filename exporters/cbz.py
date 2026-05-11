import os
import zipfile


class CBZExporter:
    name = "CBZ"
    extension = ".cbz"

    def export(self, title: str, chapter_name: str, image_paths: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_chapter = self._safe_name(chapter_name)
        os.makedirs(os.path.join(output_dir, safe_title), exist_ok=True)
        output_path = os.path.join(output_dir, safe_title, f"{safe_chapter}.cbz")

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_STORED) as zf:
            for i, img_path in enumerate(image_paths):
                ext = os.path.splitext(img_path)[1] or ".jpg"
                arcname = f"{i+1:04d}{ext}"
                zf.write(img_path, arcname)

        return output_path

    def export_volume(self, title: str, volume_name: str, chapters_data: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_vol = self._safe_name(volume_name)
        os.makedirs(os.path.join(output_dir, safe_title), exist_ok=True)
        output_path = os.path.join(output_dir, safe_title, f"{safe_vol}.cbz")

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_STORED) as zf:
            for ch_name, image_paths in chapters_data:
                safe_ch = self._safe_name(ch_name)
                for i, img_path in enumerate(image_paths):
                    ext = os.path.splitext(img_path)[1] or ".jpg"
                    arcname = f"{safe_ch}/{i+1:04d}{ext}"
                    zf.write(img_path, arcname)

        return output_path

    def _safe_name(self, name: str) -> str:
        return "".join(c if c.isalnum() or c in " -_.()" else "_" for c in name).strip()