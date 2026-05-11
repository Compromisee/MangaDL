import os
from PIL import Image


class PDFExporter:
    name = "PDF"
    extension = ".pdf"

    def export(self, title: str, chapter_name: str, image_paths: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_chapter = self._safe_name(chapter_name)
        os.makedirs(os.path.join(output_dir, safe_title), exist_ok=True)
        output_path = os.path.join(output_dir, safe_title, f"{safe_chapter}.pdf")

        images = self._load_images(image_paths)
        if not images:
            return ""

        first = images[0]
        rest = images[1:] if len(images) > 1 else []
        first.save(output_path, "PDF", save_all=True, append_images=rest, resolution=150)

        for img in images:
            img.close()

        return output_path

    def export_volume(self, title: str, volume_name: str, chapters_data: list, output_dir: str) -> str:
        safe_title = self._safe_name(title)
        safe_vol = self._safe_name(volume_name)
        os.makedirs(os.path.join(output_dir, safe_title), exist_ok=True)
        output_path = os.path.join(output_dir, safe_title, f"{safe_vol}.pdf")

        all_paths = []
        for ch_name, image_paths in chapters_data:
            all_paths.extend(image_paths)

        images = self._load_images(all_paths)
        if not images:
            return ""

        first = images[0]
        rest = images[1:] if len(images) > 1 else []
        first.save(output_path, "PDF", save_all=True, append_images=rest, resolution=150)

        for img in images:
            img.close()

        return output_path

    def _load_images(self, paths: list) -> list:
        images = []
        for p in paths:
            try:
                img = Image.open(p).convert("RGB")
                images.append(img)
            except Exception:
                continue
        return images

    def _safe_name(self, name: str) -> str:
        return "".join(c if c.isalnum() or c in " -_.()" else "_" for c in name).strip()