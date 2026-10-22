"""Fehlermeldungen auf Deutsch und Englisch.

الكود (math_solver و translator) بيرمي أخطاء بـ "مفتاح" بس، زي MathError("too_long", max=200).
الـ API بيحوّل المفتاح لنص باللغة اللي الواجهة بعتتها (lang = "de" أو "en").
عشان تضيف رسالة جديدة: حطها في اللغتين بنفس المفتاح ونفس أسماء {المتغيرات}.
"""

DEFAULT_LANG = "de"

MESSAGES = {
    "de": {
        # ---- Mathe-Löser ----
        "empty_equation": "Bitte gib eine Gleichung ein.",
        "too_long": "Die Eingabe ist zu lang (maximal {max} Zeichen).",
        "bad_chars": "Die Eingabe enthält nicht erlaubte Zeichen.",
        "dot_before_letter": "Ein Punkt vor Buchstaben ist nicht erlaubt.",
        "exponent_too_big": "Der Exponent ist zu groß.",
        "side_empty": "Eine Seite der Gleichung ist leer.",
        "parse_failed": "Ich kann diesen Ausdruck nicht verstehen: {text}",
        "bad_variable": "„{name}“ ist kein gültiger Variablenname.",
        "no_variable": "Keine Variable gefunden.",
        "many_variables": "Mehrere Variablen gefunden ({names}). Bitte wähle eine Variable.",
        "one_equals": 'Pro Gleichung ist nur ein "=" erlaubt.',
        "var_not_in_equation": "Die Variable {var} kommt in der Gleichung nicht vor.",
        "no_equals_here": 'Hier bitte kein "=" verwenden. Für Gleichungen wähle „Lösen“.',
        "need_bounds": "Für ein bestimmtes Integral brauche ich „Von“ und „Bis“.",
        "integral_unsolvable": "Dieses Integral kann ich nicht lösen.",
        "limit_unsolvable": "Diesen Grenzwert kann ich nicht berechnen.",
        "has_variables": "Der Ausdruck enthält Variablen. Für einen Zahlenwert brauche ich nur Zahlen.",
        "unknown_operation": "Diese Rechenart gibt es nicht.",
        "timeout": "Die Berechnung dauert zu lange (mehr als {seconds} Sekunden).",
        "calc_failed": "Das konnte ich nicht berechnen ({kind}).",
        "plot_no_equals": 'Für ein Diagramm bitte kein "=" verwenden. Schreibe nur die Funktion, z. B. x^2 - 4.',
        "plot_failed": "Das Diagramm konnte nicht gezeichnet werden ({kind}).",
        "plot_empty": "Für diese Funktion gibt es im Bereich -10 bis 10 keine darstellbaren Werte.",
        "plot_needs_matplotlib": "Für Diagramme fehlt das Paket matplotlib. Installiere es mit: pip install matplotlib",
        # ---- Übersetzer ----
        "enter_text": "Bitte gib einen Text ein.",
        "text_too_long": "Der Text ist zu lang (maximal {max} Zeichen).",
        "bad_target": "Diese Zielsprache gibt es nicht.",
        "bad_source": "Diese Ausgangssprache gibt es nicht.",
        "same_language": "Ausgangs- und Zielsprache sind gleich.",
        "ollama_down": "Ollama antwortet nicht. Läuft Ollama und ist das Modell {model} installiert?",
        "ollama_bad_reply": "Ollama hat eine unerwartete Antwort geschickt.",
        "empty_translation": "Ich habe keine Übersetzung bekommen. Bitte versuche es noch einmal.",
        "not_a_command": 'Das ist kein Übersetzungsbefehl. Beispiel: "translate to German: good morning"',
        # ---- Dateien ----
        "file_empty": "Die Datei ist leer.",
        "file_too_big": "Die Datei ist zu groß (maximal {max_mb} MB).",
        "file_unsupported": "Dieses Dateiformat kann ich nicht lesen ({ext}).",
        "file_unreadable": "Die Datei ist beschädigt oder kann nicht gelesen werden.",
        "pdf_needs_pypdf": "Für PDF-Dateien fehlt das Paket pypdf. Installiere es mit: pip install pypdf",
        "pdf_encrypted": "Die PDF-Datei ist mit einem Passwort geschützt.",
        "no_text_in_file": "In der Datei wurde kein Text gefunden. Gescannte PDFs und Bilder haben keine Textebene.",
        "doc_not_found": "Diese Datei gibt es nicht (mehr). Vielleicht wurde der Server neu gestartet.",
        "enter_question": "Bitte gib eine Frage ein.",
        "question_too_long": "Die Frage ist zu lang (maximal {max} Zeichen).",
        "empty_answer": "Ich habe keine Antwort bekommen. Bitte versuche es noch einmal.",
    },
    "en": {
        # ---- Math solver ----
        "empty_equation": "Please enter an equation.",
        "too_long": "The input is too long (maximum {max} characters).",
        "bad_chars": "The input contains characters that are not allowed.",
        "dot_before_letter": "A dot before letters is not allowed.",
        "exponent_too_big": "The exponent is too large.",
        "side_empty": "One side of the equation is empty.",
        "parse_failed": "I can't understand this expression: {text}",
        "bad_variable": "“{name}” is not a valid variable name.",
        "no_variable": "No variable found.",
        "many_variables": "Several variables found ({names}). Please choose a variable.",
        "one_equals": 'Only one "=" is allowed per equation.',
        "var_not_in_equation": "The variable {var} does not appear in the equation.",
        "no_equals_here": 'Please don\'t use "=" here. For equations choose "Solve".',
        "need_bounds": "For a definite integral I need both “From” and “To”.",
        "integral_unsolvable": "I can't solve this integral.",
        "limit_unsolvable": "I can't calculate this limit.",
        "has_variables": "The expression contains variables. For a numeric value I need numbers only.",
        "unknown_operation": "That operation doesn't exist.",
        "timeout": "The calculation takes too long (more than {seconds} seconds).",
        "calc_failed": "I couldn't calculate that ({kind}).",
        "plot_no_equals": 'Please don\'t use "=" for a graph. Write only the function, e.g. x^2 - 4.',
        "plot_failed": "The graph could not be drawn ({kind}).",
        "plot_empty": "This function has no values that can be drawn between -10 and 10.",
        "plot_needs_matplotlib": "The matplotlib package is missing for graphs. Install it with: pip install matplotlib",
        # ---- Translator ----
        "enter_text": "Please enter some text.",
        "text_too_long": "The text is too long (maximum {max} characters).",
        "bad_target": "That target language doesn't exist.",
        "bad_source": "That source language doesn't exist.",
        "same_language": "Source and target language are the same.",
        "ollama_down": "Ollama isn't responding. Is Ollama running and is the model {model} installed?",
        "ollama_bad_reply": "Ollama sent an unexpected reply.",
        "empty_translation": "I didn't get a translation. Please try again.",
        "not_a_command": 'That is not a translate command. Example: "translate to German: good morning"',
        # ---- Files ----
        "file_empty": "The file is empty.",
        "file_too_big": "The file is too big (maximum {max_mb} MB).",
        "file_unsupported": "I can't read this file type ({ext}).",
        "file_unreadable": "The file is damaged or can't be read.",
        "pdf_needs_pypdf": "The pypdf package is missing for PDF files. Install it with: pip install pypdf",
        "pdf_encrypted": "The PDF file is password-protected.",
        "no_text_in_file": "No text was found in the file. Scanned PDFs and images have no text layer.",
        "doc_not_found": "That file doesn't exist (anymore). The server may have been restarted.",
        "enter_question": "Please enter a question.",
        "question_too_long": "The question is too long (maximum {max} characters).",
        "empty_answer": "I didn't get an answer. Please try again.",
    },
}


def message(key, lang=DEFAULT_LANG, **params):
    """بيرجّع نص الرسالة باللغة المطلوبة. لغة مش معروفة = الألماني."""
    table = MESSAGES.get(lang) or MESSAGES[DEFAULT_LANG]
    template = table.get(key) or MESSAGES[DEFAULT_LANG].get(key, key)
    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template


class AppError(Exception):
    """خطأ ليه مفتاح رسالة. ده الأب بتاع MathError و TranslateError و TranslatorUnavailable."""

    def __init__(self, key, **params):
        super().__init__(key)
        self.key = key
        self.params = params

    def text(self, lang=DEFAULT_LANG):
        return message(self.key, lang, **self.params)

    def __str__(self):
        return self.text(DEFAULT_LANG)
