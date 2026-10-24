"""
Микросервис-переводчик (вариант 18). Локальный эмулятор без внешних зависимостей.
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("SERVICE_PORT", "5001"))

PHRASES = {
    "ru->en": {
        "здравствуйте": "hello",
        "привет": "hi",
        "добрый день": "good afternoon",
        "доброе утро": "good morning",
        "добрый вечер": "good evening",
        "спокойной ночи": "good night",
        "до свидания": "goodbye",
        "до встречи": "see you",
        "увидимся": "see you later",
        "добро пожаловать": "welcome",
        "спасибо": "thank you",
        "спасибо за помощь": "thank you for help",
        "пожалуйста": "you are welcome",
        "извините": "excuse me",
        "простите": "sorry",
        "будьте здоровы": "bless you",
        "как дела": "how are you",
        "как тебя зовут": "what is your name",
        "меня зовут": "my name is",
        "приятно познакомиться": "nice to meet you",
        "как погода": "how is the weather",
        "сколько это стоит": "how much does it cost",
        "где находится": "where is",
        "что это": "what is this",
        "кто это": "who is this",
        "я не понимаю": "i do not understand",
        "я не знаю": "i do not know",
        "я хочу": "i want",
        "я люблю": "i love",
        "я не люблю": "i do not like",
        "мне нравится": "i like it",
        "мне не нравится": "i do not like it",
        "я голоден": "i am hungry",
        "я устал": "i am tired",
        "очень хорошо": "very good",
        "очень плохо": "very bad",
        "хорошего дня": "have a nice day",
        "удачи": "good luck",
        "всего хорошего": "all the best",
        "с днем рождения": "happy birthday",
        "с новым годом": "happy new year",
    },
    "ru->de": {
        "здравствуйте": "hallo", "привет": "hallo",
        "добрый день": "guten tag", "доброе утро": "guten morgen",
        "добрый вечер": "guten abend", "спокойной ночи": "gute nacht",
        "до свидания": "auf wiedersehen", "до встречи": "bis bald",
        "добро пожаловать": "willkommen", "спасибо": "danke",
        "спасибо за помощь": "danke für die hilfe", "пожалуйста": "bitte",
        "извините": "entschuldigung", "простите": "es tut mir leid",
        "как дела": "wie geht es dir", "как тебя зовут": "wie heißt du",
        "меня зовут": "ich heiße", "приятно познакомиться": "freut mich",
        "сколько это стоит": "wie viel kostet das", "где находится": "wo ist",
        "я не понимаю": "ich verstehe nicht", "я не знаю": "ich weiß nicht",
        "я хочу": "ich möchte", "я люблю": "ich liebe",
        "очень хорошо": "sehr gut", "очень плохо": "sehr schlecht",
        "хорошего дня": "schönen tag", "удачи": "viel glück",
        "с днем рождения": "alles gute zum geburtstag",
    },
    "ru->fr": {
        "здравствуйте": "bonjour", "привет": "salut",
        "добрый день": "bonjour", "доброе утро": "bonjour",
        "добрый вечер": "bonsoir", "спокойной ночи": "bonne nuit",
        "до свидания": "au revoir", "до встречи": "à bientôt",
        "добро пожаловать": "bienvenue", "спасибо": "merci",
        "пожалуйста": "je vous en prie", "извините": "excusez-moi",
        "простите": "pardon", "как дела": "comment ça va",
        "как тебя зовут": "comment tu t appelles", "меня зовут": "je m appelle",
        "приятно познакомиться": "enchanté",
        "сколько это стоит": "combien ça coûte", "где находится": "où est",
        "я не понимаю": "je ne comprends pas", "я не знаю": "je ne sais pas",
        "я хочу": "je veux", "я люблю": "j aime",
        "очень хорошо": "très bien", "очень плохо": "très mauvais",
        "хорошего дня": "bonne journée", "удачи": "bonne chance",
        "с днем рождения": "joyeux anniversaire",
    },
    "ru->es": {
        "здравствуйте": "hola", "привет": "hola",
        "добрый день": "buenos días", "доброе утро": "buenos días",
        "добрый вечер": "buenas noches", "спокойной ночи": "buenas noches",
        "до свидания": "adiós", "до встречи": "hasta pronto",
        "добро пожаловать": "bienvenido", "спасибо": "gracias",
        "пожалуйста": "de nada", "извините": "disculpe",
        "простите": "lo siento", "как дела": "cómo estás",
        "как тебя зовут": "cómo te llamas", "меня зовут": "me llamo",
        "приятно познакомиться": "encantado",
        "сколько это стоит": "cuánto cuesta", "где находится": "dónde está",
        "я не понимаю": "no entiendo", "я не знаю": "no sé",
        "я хочу": "quiero", "я люблю": "me gusta",
        "очень хорошо": "muy bien", "очень плохо": "muy mal",
        "хорошего дня": "buen día", "удачи": "buena suerte",
        "с днем рождения": "feliz cumpleaños",
    },
    "en->ru": {
        "hello": "привет", "hi": "привет",
        "good morning": "доброе утро", "good afternoon": "добрый день",
        "good evening": "добрый вечер", "good night": "спокойной ночи",
        "goodbye": "до свидания", "see you": "до встречи",
        "see you later": "увидимся", "welcome": "добро пожаловать",
        "how are you": "как дела", "what is your name": "как тебя зовут",
        "my name is": "меня зовут", "nice to meet you": "приятно познакомиться",
        "thank you": "спасибо", "thank you for help": "спасибо за помощь",
        "you are welcome": "пожалуйста", "excuse me": "извините",
        "sorry": "простите", "how much does it cost": "сколько это стоит",
        "where is": "где находится", "what is this": "что это",
        "who is this": "кто это", "i do not understand": "я не понимаю",
        "i do not know": "я не знаю", "i want": "я хочу",
        "i love": "я люблю", "i like it": "мне нравится",
        "i am hungry": "я голоден", "i am tired": "я устал",
        "very good": "очень хорошо", "very bad": "очень плохо",
        "have a nice day": "хорошего дня", "good luck": "удачи",
        "all the best": "всего хорошего", "happy birthday": "с днем рождения",
        "happy new year": "с новым годом",
    },
}

WORDS = {
    "ru->en": {
        "мир": "world", "человек": "person", "люди": "people", "день": "day",
        "ночь": "night", "время": "time", "год": "year", "дело": "business",
        "язык": "language", "слово": "word", "текст": "text", "перевод": "translation",
        "компьютер": "computer", "программа": "program", "данные": "data",
        "база": "database", "собака": "dog", "кот": "cat",
        "книга": "book", "город": "city", "дом": "house", "вода": "water",
        "еда": "food", "музыка": "music", "фильм": "movie", "работа": "work",
        "друг": "friend", "семья": "family", "школа": "school", "студент": "student",
        "и": "and", "или": "or", "я": "i", "мы": "we", "вы": "you", "он": "he",
        "она": "she", "это": "this", "не": "not", "да": "yes", "нет": "no",
        "красный": "red", "синий": "blue", "зелёный": "green", "зеленый": "green",
        "жёлтый": "yellow", "желтый": "yellow", "чёрный": "black", "черный": "black",
        "белый": "white", "серый": "grey", "оранжевый": "orange", "розовый": "pink",
        "коричневый": "brown", "фиолетовый": "purple",
        "один": "one", "два": "two", "три": "three", "четыре": "four", "пять": "five",
        "шесть": "six", "семь": "seven", "восемь": "eight", "девять": "nine",
        "десять": "ten", "сто": "hundred", "тысяча": "thousand",
        "мама": "mother", "папа": "father", "брат": "brother", "сестра": "sister",
        "сын": "son", "дочь": "daughter", "бабушка": "grandmother",
        "дедушка": "grandfather", "жена": "wife", "муж": "husband",
        "ребёнок": "child", "ребенок": "child", "дети": "children",
        "хлеб": "bread", "молоко": "milk", "мясо": "meat", "рыба": "fish",
        "чай": "tea", "кофе": "coffee", "сок": "juice", "яблоко": "apple",
        "банан": "banana", "сыр": "cheese", "яйцо": "egg", "суп": "soup",
        "сахар": "sugar", "соль": "salt", "пицца": "pizza",
        "солнце": "sun", "луна": "moon", "звезда": "star", "небо": "sky",
        "море": "sea", "река": "river", "гора": "mountain", "лес": "forest",
        "дерево": "tree", "цветок": "flower", "дождь": "rain", "снег": "snow",
        "ветер": "wind", "огонь": "fire", "земля": "earth",
        "идти": "go", "бежать": "run", "делать": "do", "говорить": "speak",
        "видеть": "see", "слышать": "hear", "знать": "know", "думать": "think",
        "читать": "read", "писать": "write", "играть": "play", "спать": "sleep",
        "есть": "eat", "пить": "drink", "жить": "live", "любить": "love",
        "хотеть": "want", "мочь": "can", "помогать": "help",
        "большой": "big", "маленький": "small", "хороший": "good", "плохой": "bad",
        "новый": "new", "старый": "old", "быстрый": "fast", "медленный": "slow",
        "красивый": "beautiful", "интересный": "interesting", "важный": "important",
        "трудный": "difficult", "легкий": "easy", "лёгкий": "easy",
        "дорогой": "expensive", "дешевый": "cheap", "дешёвый": "cheap",
        "длинный": "long", "короткий": "short", "высокий": "high", "низкий": "low",
        "час": "hour", "минута": "minute", "секунда": "second", "неделя": "week",
        "месяц": "month", "сегодня": "today", "вчера": "yesterday",
        "завтра": "tomorrow", "утро": "morning", "вечер": "evening",
        "страна": "country", "деревня": "village", "улица": "street",
        "магазин": "shop", "офис": "office", "университет": "university",
        "ресторан": "restaurant", "больница": "hospital", "парк": "park",
        "стол": "table", "стул": "chair", "окно": "window", "дверь": "door",
        "машина": "car", "телефон": "phone", "ключ": "key", "деньги": "money",
        "часы": "clock",
        "интернет": "internet", "сайт": "website", "файл": "file",
        "папка": "folder", "сеть": "network", "сервер": "server",
        "браузер": "browser", "приложение": "application", "код": "code",
    },
    "en->ru": {
        "world": "мир", "person": "человек", "people": "люди", "day": "день",
        "night": "ночь", "time": "время", "year": "год", "language": "язык",
        "word": "слово", "text": "текст", "translation": "перевод",
        "computer": "компьютер", "program": "программа", "data": "данные",
        "database": "база данных", "dog": "собака", "cat": "кот",
        "book": "книга", "city": "город", "house": "дом", "water": "вода",
        "food": "еда", "music": "музыка", "movie": "фильм", "work": "работа",
        "friend": "друг", "family": "семья", "school": "школа", "student": "студент",
        "docker": "докер", "application": "приложение", "service": "сервис",
        "and": "и", "or": "или", "i": "я", "we": "мы", "you": "вы",
        "he": "он", "she": "она", "this": "это", "not": "не", "yes": "да", "no": "нет",
        "my": "мой", "your": "твой", "is": "есть", "are": "есть",
        "red": "красный", "blue": "синий", "green": "зелёный", "yellow": "жёлтый",
        "black": "чёрный", "white": "белый", "grey": "серый", "gray": "серый",
        "orange": "оранжевый", "pink": "розовый", "brown": "коричневый",
        "purple": "фиолетовый",
        "one": "один", "two": "два", "three": "три", "four": "четыре",
        "five": "пять", "six": "шесть", "seven": "семь", "eight": "восемь",
        "nine": "девять", "ten": "десять", "hundred": "сто", "thousand": "тысяча",
        "mother": "мама", "father": "папа", "brother": "брат", "sister": "сестра",
        "son": "сын", "daughter": "дочь", "grandmother": "бабушка",
        "grandfather": "дедушка", "wife": "жена", "husband": "муж",
        "child": "ребёнок", "children": "дети",
        "bread": "хлеб", "milk": "молоко", "meat": "мясо", "fish": "рыба",
        "tea": "чай", "coffee": "кофе", "juice": "сок", "apple": "яблоко",
        "banana": "банан", "cheese": "сыр", "egg": "яйцо", "soup": "суп",
        "sugar": "сахар", "salt": "соль", "pizza": "пицца",
        "sun": "солнце", "moon": "луна", "star": "звезда", "sky": "небо",
        "sea": "море", "river": "река", "mountain": "гора", "forest": "лес",
        "tree": "дерево", "flower": "цветок", "rain": "дождь", "snow": "снег",
        "wind": "ветер", "fire": "огонь", "earth": "земля",
        "go": "идти", "run": "бежать", "do": "делать", "speak": "говорить",
        "see": "видеть", "hear": "слышать", "know": "знать", "think": "думать",
        "read": "читать", "write": "писать", "play": "играть", "sleep": "спать",
        "eat": "есть", "drink": "пить", "live": "жить", "love": "любить",
        "want": "хотеть", "can": "мочь", "help": "помогать",
        "big": "большой", "small": "маленький", "good": "хороший", "bad": "плохой",
        "new": "новый", "old": "старый", "fast": "быстрый", "slow": "медленный",
        "beautiful": "красивый", "interesting": "интересный",
        "important": "важный", "difficult": "трудный", "easy": "легкий",
        "expensive": "дорогой", "cheap": "дешевый", "long": "длинный",
        "short": "короткий", "high": "высокий", "low": "низкий",
        "hour": "час", "minute": "минута", "second": "секунда", "week": "неделя",
        "month": "месяц", "today": "сегодня", "yesterday": "вчера",
        "tomorrow": "завтра", "morning": "утро", "evening": "вечер",
        "country": "страна", "village": "деревня", "street": "улица",
        "shop": "магазин", "office": "офис", "university": "университет",
        "restaurant": "ресторан", "hospital": "больница", "park": "парк",
        "table": "стол", "chair": "стул", "window": "окно", "door": "дверь",
        "car": "машина", "phone": "телефон", "key": "ключ", "money": "деньги",
        "clock": "часы",
        "internet": "интернет", "website": "сайт", "file": "файл",
        "folder": "папка", "network": "сеть", "server": "сервер",
        "browser": "браузер", "code": "код",
    },
    "ru->de": {
        "мир": "welt", "человек": "mensch", "день": "tag", "ночь": "nacht",
        "время": "zeit", "год": "jahr", "язык": "sprache", "слово": "wort",
        "текст": "text", "книга": "buch", "город": "stadt", "дом": "haus",
        "вода": "wasser", "друг": "freund", "работа": "arbeit", "музыка": "musik",
        "красный": "rot", "синий": "blau", "зелёный": "grün", "жёлтый": "gelb",
        "чёрный": "schwarz", "белый": "weiß",
        "один": "eins", "два": "zwei", "три": "drei", "четыре": "vier", "пять": "fünf",
        "мама": "mutter", "папа": "vater", "брат": "bruder", "сестра": "schwester",
        "хлеб": "brot", "молоко": "milch", "кофе": "kaffee",
        "солнце": "sonne", "луна": "mond", "звезда": "stern", "небо": "himmel",
        "большой": "groß", "маленький": "klein", "хороший": "gut", "плохой": "schlecht",
        "новый": "neu", "старый": "alt",
        "сегодня": "heute", "вчера": "gestern", "завтра": "morgen",
        "магазин": "geschäft", "улица": "straße", "машина": "auto",
        "компьютер": "computer", "интернет": "internet",
    },
    "ru->fr": {
        "мир": "monde", "человек": "personne", "день": "jour", "ночь": "nuit",
        "время": "temps", "год": "an", "язык": "langue", "слово": "mot",
        "текст": "texte", "книга": "livre", "город": "ville", "дом": "maison",
        "вода": "eau", "друг": "ami", "работа": "travail", "музыка": "musique",
        "кошка": "chat", "собака": "chien", "и": "et", "я": "je", "мы": "nous",
        "красный": "rouge", "синий": "bleu", "зелёный": "vert", "жёлтый": "jaune",
        "чёрный": "noir", "белый": "blanc",
        "один": "un", "два": "deux", "три": "trois", "четыре": "quatre", "пять": "cinq",
        "мама": "mère", "папа": "père", "брат": "frère", "сестра": "sœur",
        "хлеб": "pain", "молоко": "lait", "кофе": "café", "вино": "vin",
        "солнце": "soleil", "луна": "lune", "звезда": "étoile", "небо": "ciel",
        "большой": "grand", "маленький": "petit", "хороший": "bon", "плохой": "mauvais",
        "новый": "nouveau", "старый": "vieux",
        "сегодня": "aujourd hui", "вчера": "hier", "завтра": "demain",
        "магазин": "magasin", "улица": "rue", "машина": "voiture",
    },
    "ru->es": {
        "мир": "mundo", "человек": "persona", "день": "día", "ночь": "noche",
        "время": "tiempo", "год": "año", "язык": "idioma", "слово": "palabra",
        "текст": "texto", "книга": "libro", "город": "ciudad", "дом": "casa",
        "вода": "agua", "друг": "amigo", "работа": "trabajo", "музыка": "música",
        "красный": "rojo", "синий": "azul", "зелёный": "verde", "жёлтый": "amarillo",
        "чёрный": "negro", "белый": "blanco",
        "один": "uno", "два": "dos", "три": "tres", "четыре": "cuatro", "пять": "cinco",
        "мама": "madre", "папа": "padre", "брат": "hermano", "сестра": "hermana",
        "хлеб": "pan", "молоко": "leche", "кофе": "café", "вино": "vino",
        "солнце": "sol", "луна": "luna", "звезда": "estrella", "небо": "cielo",
        "большой": "grande", "маленький": "pequeño", "хороший": "bueno", "плохой": "malo",
        "новый": "nuevo", "старый": "viejo",
        "сегодня": "hoy", "вчера": "ayer", "завтра": "mañana",
        "магазин": "tienda", "улица": "calle", "машина": "coche",
    },
}

SUPPORTED_LANGUAGES = {
    "en": "Английский", "de": "Немецкий", "fr": "Французский",
    "es": "Испанский", "ru": "Русский",
}


def detect_language(text):
    cyr = len(re.findall(r"[а-яё]", text.lower()))
    lat = len(re.findall(r"[a-z]", text.lower()))
    return "ru" if cyr >= lat else "en"


def translate_text(text, target_lang):
    source_lang = detect_language(text)
    if target_lang == source_lang:
        return text, source_lang

    pair = f"{source_lang}->{target_lang}"
    if pair not in PHRASES and pair not in WORDS:
        if source_lang == "ru" and target_lang != "en":
            mid, _ = translate_text(text, "en")
            return translate_text(mid, target_lang)[0], source_lang
        if target_lang == "ru" and source_lang != "en":
            mid, _ = translate_text(text, "ru")
            return translate_text(mid, "en")[0], source_lang
        return text, source_lang

    lowered = text.lower().strip()
    for phrase, translated in sorted(
        PHRASES.get(pair, {}).items(), key=lambda item: len(item[0]), reverse=True
    ):
        if phrase in lowered:
            idx = lowered.index(phrase)
            repl = translated.capitalize() if text[idx:idx + 1].isupper() else translated
            text = text[:idx] + repl + text[idx + len(phrase):]
            lowered = text.lower()

    word_map = WORDS.get(pair, {})

    def repl_word(match):
        raw = match.group(0)
        key = raw.lower()
        if key in word_map:
            t = word_map[key]
            return t.capitalize() if raw[:1].isupper() else t
        return raw

    return re.sub(r"[А-Яа-яA-Za-z]+", repl_word, text), source_lang


def build_vocabulary():
    vocab = {}
    for pair in sorted(set(PHRASES) | set(WORDS)):
        source, target = pair.split("->")
        phrases = [
            {"source": s, "target": t, "type": "phrase"}
            for s, t in sorted(PHRASES.get(pair, {}).items())
        ]
        words = [
            {"source": s, "target": t, "type": "word"}
            for s, t in sorted(WORDS.get(pair, {}).items())
        ]
        vocab[pair] = {
            "source_lang": source, "target_lang": target,
            "items": phrases + words,
        }
    return vocab


class Handler(BaseHTTPRequestHandler):
    server_version = "TranslatorService/2.0"

    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "translator-web-service", "version": "2.0"})
        elif self.path == "/languages":
            self._send(200, {"languages": SUPPORTED_LANGUAGES})
        elif self.path == "/vocabulary":
            vocab = build_vocabulary()
            total = sum(len(p["items"]) for p in vocab.values())
            self._send(200, {"count": total, "pairs": vocab})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/translate":
            self._send(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": "некорректный JSON"})
            return
        text = (data.get("text") or "").strip()
        target_lang = (data.get("target_lang") or "").lower()
        if not text:
            self._send(400, {"error": "поле text обязательно"})
            return
        if target_lang not in SUPPORTED_LANGUAGES:
            self._send(400, {"error": f"неподдерживаемый язык: '{target_lang}'",
                             "supported": list(SUPPORTED_LANGUAGES.keys())})
            return
        translated, source_lang = translate_text(text, target_lang)
        self._send(200, {
            "original_text": text, "translated_text": translated,
            "source_lang": source_lang, "target_lang": target_lang,
            "engine": "local-emulator v2.0",
        })

    def log_message(self, fmt, *args):
        print(f"[web-service] {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"web-сервис переводчика слушает порт {PORT}")
    server.serve_forever()