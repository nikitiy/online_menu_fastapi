from typing import TypeVar

from slugify import slugify

T = TypeVar("T")


class SlugService:
    @staticmethod
    def set_slug(instance: T, name: str, slug_field: str = "slug") -> str:
        """
        Устанавливает slug для объекта в формате {base_slug}-{id}.

        Args:
            instance: Экземпляр модели
            name: Имя для генерации slug
            slug_field: Название поля slug в модели

        Returns:
            Установленный slug
        """
        base_slug = slugify(name)
        object_id = getattr(instance, "id", None)

        if object_id is None:
            raise ValueError("Объект должен иметь ID для генерации slug")

        slug = f"{base_slug}-{object_id}"
        setattr(instance, slug_field, slug)
        return slug
