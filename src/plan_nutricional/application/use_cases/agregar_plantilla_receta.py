from plan_nutricional.application.commands.commands import AgregarPlantillaRecetaCommand
from plan_nutricional.domain.exceptions import (
    PlantillaNoEncontradaError,
    RecetaCatalogoInactivaError,
    RecetaCatalogoNoEncontradaError,
)
from plan_nutricional.domain.repositories import (
    PlantillaPlanRepository,
    RecetaCatalogoRepository,
)


class AgregarPlantillaRecetaUseCase:
    def __init__(
        self,
        plantilla_repo: PlantillaPlanRepository,
        catalogo_repo: RecetaCatalogoRepository,
    ) -> None:
        self._plantilla_repo = plantilla_repo
        self._catalogo_repo = catalogo_repo

    async def ejecutar(self, cmd: AgregarPlantillaRecetaCommand) -> None:
        plantilla = await self._plantilla_repo.obtener_por_id(cmd.plantilla_id)
        if plantilla is None:
            raise PlantillaNoEncontradaError(cmd.plantilla_id)

        receta_catalogo = await self._catalogo_repo.obtener_por_id(cmd.receta_catalogo_id)
        if receta_catalogo is None:
            raise RecetaCatalogoNoEncontradaError(cmd.receta_catalogo_id)
        if not receta_catalogo.activa:
            raise RecetaCatalogoInactivaError(cmd.receta_catalogo_id)

        plantilla.agregar_receta(
            numero_dia=cmd.numero_dia,
            tipo=cmd.tipo,
            receta_catalogo_id=cmd.receta_catalogo_id,
            cantidad=cmd.cantidad,
            unidad=cmd.unidad,
        )
        await self._plantilla_repo.guardar(plantilla)
