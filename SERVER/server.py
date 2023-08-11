from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from retrieval import clean_tmp_dir

import routers.aoi as aoi_router
import routers.ingest as ingest_router
import routers.datasets as ds_router
import routers.spatial_index as si_router
import routers.tile as tile_router

clean_tmp_dir()
print("Tmp dir cleaned")
app = FastAPI()
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(aoi_router.router)
app.include_router(ingest_router.router)
app.include_router(ds_router.router)
app.include_router(si_router.router)
app.include_router(tile_router.router)



