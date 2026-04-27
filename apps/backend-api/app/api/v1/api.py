from fastapi import APIRouter

from app.api.v1.endpoints import auth, drift, feedback, health, model_info, my_predictions, ops, patients, pipeline, predict, predictions, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(model_info.router)
api_router.include_router(auth.router)
api_router.include_router(my_predictions.router)
api_router.include_router(predict.router)
api_router.include_router(predictions.router)
api_router.include_router(patients.router)
api_router.include_router(users.router)
api_router.include_router(feedback.router)
api_router.include_router(drift.router)
api_router.include_router(pipeline.router)
api_router.include_router(ops.router)
