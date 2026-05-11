import os
import shutil


class ImageExporter:
    name = "Images"
    extension = ""

    def export(self, title: str, chapter_name: str, image_paths: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_chapter = self._safe_name(chapter_name)
        chapter_dir = os.path.join(output_dir, safe_title, safe_chapter)
        os.makedirs(chapter_dir, exist_ok=True)

        for i, img_path in enumerate(image_paths):
            ext = os.path.splitext(img_path)[1] or ".jpg"
            dest = os.path.join(chapter_dir, f"{i+1:04d}{ext}")
            shutil.copy2(img_path, dest)

        return chapter_dir

    def export_volume(self, title: str, volume_name: str, chapters_data: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_vol = self._safe_name(volume_name)
        vol_dir = os.path.join(output_dir, safe_title, safe_vol)
        os.makedirs(vol_dir, exist_ok=True)

        for ch_name, image_paths in chapters_data:
            safe_ch = self._safe_name(ch_name)
            ch_dir = os.path.join(vol_dir, safe_ch)
            os.makedirs(ch_dir, exist_ok=True)
            for i, img_path in enumerate(image_paths):
                ext = os.path.splitext(img_path)[1] or ".jpg"
                dest = os.path.join(ch_dir, f"{i+1:04d}{ext}")
                shutil.copy2(img_path, dest)

        return vol_dir

    def _safe_name(self, name: str) -> str:
        return "".join(c if c.isalnum() or c in " -_.()" else "_" for c in name).strip()