from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel

import documents
import math_solver
import translator
from botAI import start_robot, stop_robot
from sound import find_sound, list_sounds, play_word

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"   


class MathRequest(BaseModel):
    expression: str
    operation: str
    variable: Optional[str] = None
    point: Optional[str] = None
    lower: Optional[str] = None
    upper: Optional[str] = None
    lang: str = "de"        


class TranslateRequest(BaseModel):
    text: str
    target: str
    source: str = "auto"
    lang: str = "de"


class TranslateCommandRequest(BaseModel):
    command: str          
    source: str = "auto"
    lang: str = "de"


class AskRequest(BaseModel):
    doc_id: int
    question: str
    lang: str = "de"



@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")



@app.get("/assets/{name}")
def asset(name: str):
    path = ASSETS_DIR / name
    if path.parent != ASSETS_DIR or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


@app.get("/sounds")
def sounds():
    return list_sounds()


@app.get("/play/{word}")
def play_api(word: str):
    if find_sound(word) is None:
        raise HTTPException(status_code=404, detail="Word not found")
    if not play_word(word):
        raise HTTPException(status_code=503, detail="Audio file not found (Sound_1.mp3 / Sound.mp3)")
    return {"status": "played", "word": word}

@app.get("/hi")
def hi():
    if start_robot():
        return {"status": "robot started"}
    return {"status": "robot is already running"}


@app.get("/bye")
def bye():
    stop_robot()
    return {"status": "robot stopping"}

@app.get("/math/operations")
def math_operations():
    return math_solver.operations_list()


@app.post("/math/solve")
def math_solve(req: MathRequest):
    try:
        return math_solver.solve(
            req.expression, req.operation,
            req.variable, req.point, req.lower, req.upper,
        )
    except math_solver.MathError as error:
        raise HTTPException(status_code=400, detail=error.text(req.lang))


@app.get("/math/history")
def math_history():
    return math_solver.get_history()


@app.delete("/math/history")
def math_history_clear():
    math_solver.clear_history()
    return {"status": "cleared"}


@app.get("/math/plot")
def math_plot(expression: str, var: str = "x", lang: str = "de"):
    try:
        return {"status": "success", "image": math_solver.plot_expression(expression, var)}
    except math_solver.MathError as error:
        raise HTTPException(status_code=400, detail=error.text(lang))



@app.get("/translate/languages")
def translate_languages():
    return translator.info()


@app.post("/translate")
def translate_api(req: TranslateRequest):
    try:
        return translator.translate(req.text, req.target, req.source)
    except translator.TranslateError as error:
        raise HTTPException(status_code=400, detail=error.text(req.lang))
    except translator.TranslatorUnavailable as error:
        raise HTTPException(status_code=503, detail=error.text(req.lang))



@app.post("/translate/command")
def translate_command_api(req: TranslateCommandRequest):
    try:
        return translator.translate_command(req.command, req.source)
    except translator.TranslateError as error:
        raise HTTPException(status_code=400, detail=error.text(req.lang))
    except translator.TranslatorUnavailable as error:
        raise HTTPException(status_code=503, detail=error.text(req.lang))



def _doc_error(error, lang):
    return HTTPException(status_code=getattr(error, "status", 400), detail=error.text(lang))



@app.get("/files/info")
def files_info():
    return documents.info()


@app.get("/files")
def files_list():
    return documents.list_documents()



@app.post("/files/upload")
async def files_upload(request: Request, name: str = "file", lang: str = "de"):
    try:
        declared = request.headers.get("content-length")
        if declared and declared.isdigit():
            documents.check_size(int(declared))
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            documents.check_size(len(data))
        return await run_in_threadpool(documents.add_document, name, bytes(data))
    except documents.DocumentError as error:
        raise _doc_error(error, lang)


@app.post("/files/ask")
def files_ask(req: AskRequest):
    try:
        return documents.ask(req.doc_id, req.question)
    except documents.DocumentError as error:
        raise _doc_error(error, req.lang)


@app.get("/files/{doc_id}")
def files_get(doc_id: int, lang: str = "de"):
    try:
        return documents.get_document(doc_id)
    except documents.DocumentError as error:
        raise _doc_error(error, lang)


@app.delete("/files/{doc_id}")
def files_delete(doc_id: int, lang: str = "de"):
    try:
        documents.delete_document(doc_id)
        return {"status": "deleted"}
    except documents.DocumentError as error:
        raise _doc_error(error, lang)


@app.delete("/files/{doc_id}/chat")
def files_clear_chat(doc_id: int, lang: str = "de"):
    try:
        documents.clear_chat(doc_id)
        return {"status": "cleared"}
    except documents.DocumentError as error:
        raise _doc_error(error, lang)



@app.post("/translate/document")
async def translate_document_api(request: Request, name: str = "file", target: str = "ar",
                                 source: str = "auto", lang: str = "de"):
    try:
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            documents.check_size(len(data))

        def work():
            text = documents.read_text(name, bytes(data))
            return translator.translate_document(text, target, source)

        return await run_in_threadpool(work)
    except documents.DocumentError as error:
        raise _doc_error(error, lang)
    except translator.TranslateError as error:
        raise HTTPException(status_code=400, detail=error.text(lang))
    except translator.TranslatorUnavailable as error:
        raise HTTPException(status_code=503, detail=error.text(lang))
