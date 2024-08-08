from fastapi import APIRouter

router = APIRouter(
    prefix="/items"
)


@router.get("/")
async def get_all_items():
    ...


@router.get("/{item_id}")
async def get_item(item_id: str):
    ...


@router.post("/")
async def create_item():
    ...


@router.delete("/{item_id}")
async def delete_item():
    ...


@router.patch("/{item_id}")
async def update_item(item_id: str):
    ...


@router.post("/{item_id}/photo")
async def create_photo(item_id: str):
    ...


@router.delete("/{item_id}/photo/{photo_id}")
async def delete_photo(item_id: str, photo_id: str):
    ...


@router.get("/seller/{seller_id}")
async def get_seller_items(seller_id: str):
    ...
