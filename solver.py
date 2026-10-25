"""
Core Solver and API Client for PrihorivaHori.cz (and sister sites).
Supports Czech (cs), Slovak (sk), Polish (pl), Croatian (hr), and German (de).
"""

import json
import os
import random
import string
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Dict, Generator, List, Optional, Tuple

SERVER_URL = "https://backend-dot-prihoriva.ew.r.appspot.com"
FIREBASE_API_KEY = "AIzaSyAastCJ-3Kvrdu1E29lxYW2wEIy3o38zMM"

def _load_gemini_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip("'\"")
        except Exception:
            pass
    return ""

GEMINI_API_KEY = _load_gemini_api_key()

FIREBASE_SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
FIREBASE_REFRESH_URL = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"

LANG_SITES = {
    "cs": "prihorivahori.cz",
    "sk": "prihorieva.sk",
    "pl": "cieplogoraco.pl",
    "hr": "toplije.app",
    "de": "wirdwaermer.de",
}

ANCHOR_DOMAINS_MAP = {
    "vozidlo": ["doprava_silnice_auta", "doprava_koleje_vlaky", "doprava_letectvi_kosmonautika", "doprava_vodni_lode"],
    "doprava": ["doprava_silnice_auta", "doprava_koleje_vlaky", "doprava_letectvi_kosmonautika", "doprava_vodni_lode"],
    "technologie": ["technika_pocitace_it", "technika_naradi_dilna", "doprava_letectvi_kosmonautika", "veda_vyzkum_obory"],
    "jídlo": ["jidlo_pecivo_mouka", "jidlo_ovoce_plody", "jidlo_zelenina_houby", "jidlo_maso_uzeniny", "jidlo_mlecne_syry", "jidlo_sladkosti_cukrovinky", "jidlo_napoje_alkohol", "jidlo_vareni_koreni"],
    "zvíře": ["priroda_savci_domaci", "priroda_savci_divoci", "priroda_savci_exoticti", "priroda_ptaci", "priroda_vodni_zivocisi", "priroda_hmyz"],
    "příroda": ["priroda_stromy_les", "priroda_rostliny_kvety", "priroda_krajina_hory", "priroda_voda_reky_more", "priroda_pocasi_klima", "vesmir_astronomie"],
    "dřevo": ["priroda_stromy_les", "domov_nabytek_vybaveni", "technika_naradi_dilna", "stavba_dum_architektura"],
    "čas": ["priroda_pocasi_klima", "akce_konference_zasedani", "mysl_jazyk_emoce"],
    "práce": ["lide_profese_remesla", "obchod_trh_nakup", "akce_konference_zasedani"],
    "zdraví": ["zdravi_leky_lecba", "zdravi_nemoci_poruchy", "zdravi_nemocnice_doktor", "telo_anatomie_vnejsi", "telo_organy_vnitrni"],
    "člověk": ["lide_rodina_pribuzni", "lide_profese_remesla", "telo_anatomie_vnejsi"],
    "kov": ["chemie_mineraly_kovy", "technika_naradi_dilna"],
    "věda": ["veda_vyzkum_obory", "chemie_mineraly_kovy", "vesmir_astronomie"],
    "hudba": ["kultura_hudba_nastroje"],
    "stavba": ["stavba_dum_architektura", "domov_nabytek_vybaveni"],
    "oblečení": ["obleceni_moda_doplnky"],
    "sport": ["sport_hry_souteze"],
    "umění": ["kultura_literatura_divadlo_film"],
    "obchod": ["obchod_trh_nakup", "finance_penize_banky"],
    "právo": ["pravo_soud_zakony", "politika_stat_sprava"],
    "rodina": ["lide_rodina_pribuzni"],
    "škola": ["vzdelavani_skola_akademie"],
}


def get_temperature_info(score: float) -> Tuple[str, str, str]:
    """
    Returns (label, hex_color, emoji) for a given similarity percentage (0-100).
    Matches the official game logic:
    score <= 30: #83B5D1 (Zima)
    score <= 50: #a68ee6 (Chladno)
    score <= 70: #FD80D1 (Teplo)
    score <= 85: #FF8F5C (Horko / Přihořívá)
    score > 85:  #FF5D5D (Pálí / Hoří)
    """
    if score >= 100.0:
        return "HOŘÍ!", "#FF3B30", "🏆"
    elif score >= 95.0:
        return "Pálí!", "#FF5D5D", "🔥"
    elif score >= 85.0:
        return "Přihořívá!", "#FF8F5C", "💥"
    elif score >= 70.0:
        return "Teplo", "#FD80D1", "☀️"
    elif score >= 50.0:
        return "Chladno", "#a68ee6", "☁️"
    else:
        return "Zima", "#83B5D1", "❄️"


class PrihorivaSolver:
    def __init__(
        self,
        lang: str = "cs",
        mode: str = "daily",
        user_id: Optional[str] = None,
        data_dir: Optional[str] = None,
        delay_sec: float = 0.35,
    ):
        self.lang = lang
        self.mode = mode  # "daily" or "mega" (weekly)
        self.delay_sec = delay_sec
        self.user_id = user_id or self._generate_user_id()
        self.ai_candidates = []
        self.ai_last_requested_words = ""

        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.data_dir = data_dir

        # Load language-specific clusters if available, else fallback to default clusters.json
        cluster_file = f"clusters_{self.lang}.json"
        if not os.path.exists(os.path.join(self.data_dir, cluster_file)):
            cluster_file = "clusters.json"
        self.clusters = self._load_json(cluster_file, default={"anchors": [], "domains": {}})

        # Load language-specific vocabulary if available, else fallback to words_cs.json
        vocab_file = f"words_{self.lang}.json"
        if not os.path.exists(os.path.join(self.data_dir, vocab_file)):
            vocab_file = "words_cs.json"
        self.vocab = self._load_json(vocab_file, default=[])
        self.valid_search_words: set = set(self.vocab)

        self.guesses_history: List[Dict] = []
        self.guessed_words: set = set()
        self.is_won = False
        self.winning_word: Optional[str] = None
        self._game_day = time.strftime("%Y-%m-%d")
        self._word_hash = ""
        self.last_error: str = ""

        # Indexace pro sémantickou asociaci a stoupání
        self.word_to_domains: Dict[str, set] = {}
        for d_key, d_info in self.clusters.get("domains", {}).items():
            for w in d_info.get("words", []):
                self.word_to_domains.setdefault(w, set()).add(d_key)
            for t in d_info.get("triggers", []):
                self.word_to_domains.setdefault(t, set()).add(d_key)

        for a_word, a_doms in ANCHOR_DOMAINS_MAP.items():
            for d_key in a_doms:
                self.word_to_domains.setdefault(a_word, set()).add(d_key)

        # Skupiny domén podle tematických rodin (doprava_*, jidlo_*, priroda_*, veda_*, technika_*, atd.)
        self.domain_families: Dict[str, List[str]] = {}
        for d_key in self.clusters.get("domains", {}).keys():
            family = d_key.split("_")[0]
            self.domain_families.setdefault(family, []).append(d_key)

        # Morfologické vzorce pro inteligentní cross-matching
        self.suffix_groups: Dict[str, set] = {
            "latin_ium": {w for w in self.vocab if (w.endswith("ium") or w.endswith("um")) and len(w) > 4},
            "action_ani": {w for w in self.vocab if (w.endswith("ání") or w.endswith("ení")) and len(w) > 4},
            "formal_ence": {w for w in self.vocab if (w.endswith("ence") or w.endswith("ance")) and len(w) > 4},
            "action_ace": {w for w in self.vocab if w.endswith("ace") and len(w) > 4},
            "quality_ost": {w for w in self.vocab if w.endswith("ost") and len(w) > 4},
        }

        # Načtení metadat o aktuální hře a tajném slovu
        self._init_game_meta()

        # Obnovení historie z předchozího spuštění pro dnešní hru
        self.load_session()

    def get_candidate_recommendations(self, limit: int = 40) -> List[str]:
        """
        Inteligentní generátor kandidátů pro sémantické stoupání (Adaptive Hill-Climbing).
        Analyzuje dosavadní úspěšné pokusy a přiřazuje váhy netestovaným slovům na základě:
        1. Přítomnosti v doménách s nejvyššími skóre (exponenciální vážení podle podobnosti).
        2. Morfologické rezonance (shoda sufixu a registru, např. -ium, -ání, -ence).
        3. Lexikální kořenové příbuznosti.
        Vrací seřazený seznam netestovaných slov od nejnadějnějších.
        """
        if not self.guesses_history:
            return []

        # Výběr nejlepších dosavadních pokusů (sémantické majáky)
        valid_history = [
            g for g in self.guesses_history
            if g.get("raw_similarity", 0.0) > 0.0
        ]
        if not valid_history:
            return []

        sorted_guesses = sorted(valid_history, key=lambda x: x["raw_similarity"], reverse=True)
        beacons = sorted_guesses[:8]
        top_best = beacons[0]
        top_sim = top_best["raw_similarity"]

        # Pokud ani nejlepší slovo nemá aspoň 35%, sémantické okolí ještě není zřejmé
        if top_sim < 0.35:
            return []

        candidate_scores: Dict[str, float] = {}

        # 1. Analýza sémantických domén kolem majáků
        for b in beacons:
            b_word = b["word"]
            b_sim = b["raw_similarity"]
            # Exponenciální váha: čím vyšší skóre majáku, tím dramaticky vyšší váha jeho sousedů
            b_weight = (b_sim ** 3) * 25.0

            # Prozkoumáme domény, do kterých maják spadá
            doms = self.word_to_domains.get(b_word, set())
            for d_key in doms:
                d_info = self.clusters.get("domains", {}).get(d_key, {})
                d_words = d_info.get("words", [])
                # Multiplikátor specifičnosti: menší, těsnější domény mají vyšší prioritu
                spec_mult = min(2.5, 45.0 / max(15, len(d_words)))
                effective_weight = b_weight * spec_mult

                for t in d_info.get("triggers", []):
                    if t not in self.guessed_words and self.is_valid_search_word(t):
                        candidate_scores[t] = candidate_scores.get(t, 0.0) + effective_weight * 1.5

                for w in d_words:
                    if w not in self.guessed_words and self.is_valid_search_word(w):
                        # Základní krátká slova mají lehký bonus oproti dlouhým složeninám
                        brevity_bonus = max(0.0, 3.0 - len(w) * 0.15)
                        candidate_scores[w] = candidate_scores.get(w, 0.0) + effective_weight + brevity_bonus

                # Posílíme sesterské domény ve stejné tematické rodině (např. letectví a kosmonautika při zásahu silniční dopravy)
                family = d_key.split("_")[0]
                for sister_key in self.domain_families.get(family, []):
                    if sister_key != d_key:
                        s_info = self.clusters.get("domains", {}).get(sister_key, {})
                        for t in s_info.get("triggers", []):
                            if t not in self.guessed_words and self.is_valid_search_word(t):
                                candidate_scores[t] = candidate_scores.get(t, 0.0) + effective_weight * 0.8
                        for sw in s_info.get("words", []):
                            if sw not in self.guessed_words and self.is_valid_search_word(sw):
                                candidate_scores[sw] = candidate_scores.get(sw, 0.0) + effective_weight * 0.4

            # 2. Morfologická rezonance
            for g_name, g_words in self.suffix_groups.items():
                if b_word in g_words:
                    for w in g_words:
                        if w not in self.guessed_words and self.is_valid_search_word(w):
                            match_bonus = 0.0
                            if self.word_to_domains.get(w, set()) & doms:
                                match_bonus += b_weight * 1.2
                            elif b_sim >= 0.80:
                                match_bonus += b_weight * 0.5
                            if match_bonus > 0:
                                candidate_scores[w] = candidate_scores.get(w, 0.0) + match_bonus

            # 3. Kořenová shoda (pouze pro horká specifická slova b_sim >= 0.82 s kmenem >= 5 písmen)
            # Vyřazujeme generické předpony jako 'auto', 'dopr', 'stav', které zaplavují kandidáty nesouvisejícími slovy
            GENERIC_STEMS = {"auto", "dopr", "techn", "vedec", "stav", "skol", "prist", "odlet"}
            if b_sim >= 0.82 and len(b_word) >= 5:
                b_root = b_word[:5]
                if b_root not in GENERIC_STEMS:
                    for w in self.vocab:
                        if w not in self.guessed_words and w.startswith(b_root) and w != b_word:
                            candidate_scores[w] = candidate_scores.get(w, 0.0) + (b_sim ** 2) * 6.0

        # Pokud jsme v režimu PŘIHOŘÍVÁ (>= 85%), masivně podpoříme slova z nejužšího okolí top majáků
        if top_sim >= 0.85:
            top_doms = self.word_to_domains.get(top_best["word"], set())
            for d_key in top_doms:
                d_info = self.clusters.get("domains", {}).get(d_key, {})
                for t in d_info.get("triggers", []):
                    if t not in self.guessed_words and self.is_valid_search_word(t):
                        candidate_scores[t] = candidate_scores.get(t, 0.0) + 150.0
                for w in d_info.get("words", []):
                    if w not in self.guessed_words and self.is_valid_search_word(w):
                        brevity_bonus = max(0.0, 5.0 - len(w) * 0.3)
                        candidate_scores[w] = candidate_scores.get(w, 0.0) + 100.0 + brevity_bonus

        if not candidate_scores:
            return []

        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_candidates[:limit]]

    def _init_game_meta(self):
        """Načte aktuální herní den/týden a hash tajného slova ze serveru."""
        today_str = time.strftime("%Y-%m-%d")
        default_day = time.strftime("%Y-W%W") if self.mode == "mega" else today_str
        self._game_day = default_day
        self._word_hash = ""
        try:
            poll = self.get_poll_stats()
            if isinstance(poll, dict):
                if self.mode == "mega":
                    self._game_day = poll.get("weekly_stats", {}).get("iso_week", default_day)
                    self._word_hash = poll.get("weekly_word_hash", "")
                else:
                    self._game_day = poll.get("game_day", today_str)
                    self._word_hash = poll.get("word_hash", "")
        except Exception:
            pass

    def _generate_user_id(self) -> str:
        rand_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
        return f"user_solver_{rand_str}_{int(time.time())}"

    def _get_mega_auth_filepath(self) -> str:
        sessions_dir = os.path.join(self.data_dir, "sessions")
        return os.path.join(sessions_dir, f"auth_mega_{self.lang}.json")

    def _get_mega_auth(self, force_refresh: bool = False, force_new: bool = False) -> Tuple[str, str]:
        """
        Zajistí platný autentizační Firebase token pro týdenní megaslovo (/weekly/similarity).
        Pokud ještě neexistuje účet nebo vypršel limit pokusů (429), automaticky vytvoří nový.
        Pokud token vypršel (3600s), automaticky ho obnoví přes refresh token.
        Vrací (id_token, local_id).
        """
        path = self._get_mega_auth_filepath()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not force_new and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                token = data.get("id_token")
                local_id = data.get("local_id")
                refresh_token = data.get("refresh_token")
                expires_at = data.get("expires_at", 0)

                # Pokud token existuje a nevypršel ani není vyžádán refresh
                if not force_refresh and token and local_id and expires_at > time.time() + 60:
                    return token, local_id

                # Obnova tokenu přes refresh_token
                if refresh_token:
                    try:
                        refresh_data = urllib.parse.urlencode({
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            FIREBASE_REFRESH_URL,
                            data=refresh_data,
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                        )
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            res = json.loads(resp.read().decode("utf-8"))
                            data["id_token"] = res.get("id_token", token)
                            data["refresh_token"] = res.get("refresh_token", refresh_token)
                            data["expires_at"] = time.time() + int(res.get("expires_in", 3600))
                            with open(path, "w", encoding="utf-8") as f_out:
                                json.dump(data, f_out, indent=2)
                            return data["id_token"], data.get("local_id", local_id)
                    except Exception as e:
                        print(f"[Mega Auth] Obnova tokenu selhala, zakládám nový řešitelský účet: {e}")
            except Exception as e:
                print(f"[Mega Auth] Chyba při čtení auth souboru: {e}")

        # Vytvoření nového řešitelského účtu přes Firebase Identity Toolkit
        rand_id = random.randint(100000, 999999)
        email = f"solver_{self.lang}_{int(time.time())}_{rand_id}@example.com"
        pwd = f"MegaSolv_{rand_id}!"
        signup_payload = json.dumps({
            "email": email,
            "password": pwd,
            "returnSecureToken": True,
        }).encode("utf-8")
        req = urllib.request.Request(
            FIREBASE_SIGNUP_URL,
            data=signup_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            saved = {
                "email": email,
                "password": pwd,
                "local_id": res["localId"],
                "id_token": res["idToken"],
                "refresh_token": res["refreshToken"],
                "expires_at": time.time() + int(res.get("expiresIn", 3600)),
            }
            with open(path, "w", encoding="utf-8") as f_out:
                json.dump(saved, f_out, indent=2)
            return saved["id_token"], saved["local_id"]

    def get_session_filepath(self) -> str:
        sessions_dir = os.path.join(self.data_dir, "sessions")
        return os.path.join(sessions_dir, f"session_{self.lang}_{self.mode}.json")

    def load_session(self) -> bool:
        """
        Načte historii z předchozího spuštění hádání pro daný jazyk a herní režim,
        pokud odpovídá aktuálnímu hernímu dni / týdnu a tajnému slovu.
        """
        path = self.get_session_filepath()
        if not os.path.exists(path):
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            saved_day = data.get("game_day", "")
            saved_hash = data.get("word_hash", "")

            # Porovnání s aktuální hrou
            is_same_game = False
            if self._word_hash and saved_hash:
                is_same_game = (self._word_hash == saved_hash)
            elif saved_day:
                is_same_game = (saved_day == self._game_day)

            if not is_same_game:
                return False

            self.user_id = data.get("user_id", self.user_id)
            self.guesses_history = data.get("guesses", [])
            self.guessed_words = {g["word"] for g in self.guesses_history}
            self.is_won = data.get("is_won", False)
            self.winning_word = data.get("winning_word", None)
            return True
        except Exception as e:
            print(f"[Warn] Nelze načíst předchozí historii {path}: {e}")
            return False

    def save_session(self):
        """
        Uloží aktuální stav hádání na disk pro možnost navázání při dalším spuštění.
        """
        path = self.get_session_filepath()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            payload = {
                "lang": self.lang,
                "mode": self.mode,
                "game_day": self._game_day,
                "word_hash": self._word_hash,
                "user_id": self.user_id,
                "is_won": self.is_won,
                "winning_word": self.winning_word,
                "updated_at": time.time(),
                "guesses": self.guesses_history,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Warn] Nelze uložit historii do {path}: {e}")

    def clear_session(self):
        """
        Vymaže uloženou historii pro daný jazyk a herní režim.
        """
        self.guesses_history = []
        self.guessed_words = set()
        self.is_won = False
        self.winning_word = None
        path = self.get_session_filepath()
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def _load_json(self, filename: str, default):
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warn] Could not load {path}: {e}")
        return default

    def is_valid_search_word(self, word: str) -> bool:
        """
        Ověří, zda slovo splňuje podmínku hry a sémantického hledání:
        běžné české slovo v jednotném čísle a v 1. pádě (nominativ singuláru).
        Slova, která nesplňují tuto podmínku, se do hledání nezahrnují.
        """
        word = word.strip().lower()
        if not word or " " in word:
            return False
        if self.lang == "cs":
            return word in self.valid_search_words
        return True

    def get_poll_stats(self) -> Dict:
        """Fetch game metadata, date, stats, and word_hash."""
        url = f"{SERVER_URL}/poll"
        headers = {"X-Lang": self.lang}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def get_yesterdays_word(self) -> str:
        """
        Vrátí předchozí tajné slovo:
        - pro denní režim včerejší slovo (/yesterdays_word)
        - pro týdenní režim minulé týdenní slovo (/weekly/last_word)
        """
        endpoint = "/weekly/last_word" if self.mode == "mega" else "/yesterdays_word"
        url = f"{SERVER_URL}{endpoint}"
        headers = {"X-Lang": self.lang}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("last_word" if self.mode == "mega" else "yesterdays_word", "")
        except Exception:
            return ""

    def submit_guess(
        self, word: str, enforce_valid: bool = False, retry_count: int = 0
    ) -> Optional[float]:
        """
        Sends a single guess to the backend.
        Returns the similarity score (0.0 to 1.0) or None on error/typo/invalid word.
        If word was already guessed in this session, returns cached score.
        Automatically handles Firebase authentication and rate limits for mega mode.
        """
        word = word.strip().lower()
        if not word:
            return None

        # Pokud již slovo bylo v této relaci otestováno, vrátíme jeho známé skóre
        if word in self.guessed_words:
            for entry in self.guesses_history:
                if entry["word"] == word:
                    return entry["raw_similarity"]
            return None

        # Slova nesplňující podmínku (běžná slova v jednotném čísle a 1. pádě) do hledání nezahrnovat
        if enforce_valid and not self.is_valid_search_word(word):
            self.last_error = "Slovo nesplňuje pravidla: Hledaná slova jsou pouze běžná slova v jednotném čísle a 1. pádě."
            return None

        guess_number = len(self.guesses_history) + 1
        endpoint = "/weekly/similarity" if self.mode == "mega" else "/similarity"
        url = f"{SERVER_URL}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "X-Lang": self.lang,
            "X-User-ID": self.user_id,
        }

        # V režimu mega (týdenní hra) vyžaduje backend autentizovaného Firebase uživatele
        if self.mode == "mega":
            try:
                auth_token, auth_uid = self._get_mega_auth()
                headers["Authorization"] = f"Bearer {auth_token}"
                headers["X-User-ID"] = auth_uid
            except Exception as e:
                self.last_error = f"Chyba autentizace pro megaslovo: {e}"
                return None

        payload = json.dumps({"word1": word, "guesses": guess_number}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                raw_sim = float(res.get("similarity", 0.0))

                # Server recommendations
                cooldown_ms = res.get("recommended_cooldown", 500)
                actual_delay = max(self.delay_sec, cooldown_ms / 1000.0)

                # Rounding as done by the frontend
                score_pct = round(raw_sim * 100, 2)
                label, color, emoji = get_temperature_info(score_pct)

                entry = {
                    "number": guess_number,
                    "word": word,
                    "raw_similarity": raw_sim,
                    "score_pct": score_pct,
                    "label": label,
                    "color": color,
                    "emoji": emoji,
                    "timestamp": time.time(),
                }

                if self.mode == "mega":
                    mega_left = res.get("mega_attempts_left")
                    if mega_left is not None:
                        entry["mega_attempts_left"] = mega_left

                self.guessed_words.add(word)
                self.guesses_history.append(entry)

                if raw_sim >= 0.9999 or score_pct >= 100.0:
                    self.is_won = True
                    self.winning_word = word
                    if self.mode == "daily":
                        self._increment_win_counter()

                # Průběžně ukládáme relaci pro možnost navázání při dalším spuštění
                self.save_session()

                time.sleep(actual_delay)
                return raw_sim

        except urllib.error.HTTPError as e:
            # Režim mega: pokud vypršel token (401) nebo byl dosažen limit pokusů (429), automaticky vyřešíme
            if self.mode == "mega" and retry_count < 2:
                if e.code == 401:
                    try:
                        self._get_mega_auth(force_refresh=True)
                        return self.submit_guess(word, enforce_valid, retry_count=retry_count + 1)
                    except Exception:
                        pass
                elif e.code == 429:
                    try:
                        self._get_mega_auth(force_new=True)
                        return self.submit_guess(word, enforce_valid, retry_count=retry_count + 1)
                    except Exception:
                        pass

            try:
                err_data = json.loads(e.read().decode("utf-8"))
                self.last_error = err_data.get("error", f"HTTP {e.code}")
            except Exception:
                self.last_error = f"HTTP {e.code}: {e.reason}"
            return None

        except Exception as e:
            self.last_error = str(e)
            return None

    def _increment_win_counter(self):
        """Call /increment_correct_guesses to register the win on the server."""
        url = f"{SERVER_URL}/increment_correct_guesses"
        headers = {
            "Content-Type": "application/json",
            "X-Lang": self.lang,
            "X-User-ID": self.user_id,
        }
        req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def solve_generator(self, max_guesses: int = 150) -> Generator[Dict, None, None]:
        """
        Autonomous solving generator.
        Yields status dicts after each step so UIs or CLI can display live updates.
        Resumes seamlessly taking into account all words from previous guessing.
        """
        mode_label = "MEGASLOVO (TÝDENNÍ HRA)" if self.mode == "mega" else "DENNÍ HRA"
        yield {
            "type": "start",
            "lang": self.lang,
            "mode": self.mode,
            "user_id": self.user_id,
            "message": f"Zahajuji řešení ({mode_label} - {self.lang.upper()})",
        }

        # 0. Pokud již bylo tajné slovo odhaleno dříve
        if self.is_won and self.winning_word:
            yield {
                "type": "win",
                "word": self.winning_word,
                "total": len(self.guesses_history),
                "already_won": True,
                "message": f"Tajné slovo '{self.winning_word.upper()}' již bylo v předchozím hádání úspěšně odhaleno!",
            }
            return

        # Pokud existují předchozí pokusy z dnešního hádání, navážeme na ně
        if self.guesses_history:
            prev_best = self.get_best_guess()
            yield {
                "type": "resumed",
                "count": len(self.guesses_history),
                "best": prev_best,
                "guesses": self.guesses_history,
                "message": f"Pokračuji v luštění: načteno {len(self.guesses_history)} slov z předchozího hádání (dosud nejlepší: '{prev_best['word']}' {prev_best['score_pct']}%).",
            }

        # Cílový limit: umožní přidat pokusy, i pokud bylo již dříve dosaženo hranice
        target_limit = max_guesses if max_guesses > len(self.guesses_history) else len(self.guesses_history) + max_guesses

        # Slovník všech dosud otestovaných slov a jejich skóre
        known_scores: Dict[str, float] = {
            g["word"]: g["raw_similarity"] for g in self.guesses_history
        }

        # 1. FÁZE: Strategické sondování kotev (Global Probing)
        yield {"type": "phase", "phase": 1, "title": "Strategické sondování sémantických kotev"}
        anchors = self.clusters.get("anchors", [])

        anchor_scores: Dict[str, float] = {}
        for anchor in anchors:
            if self.is_won or len(self.guesses_history) >= target_limit:
                break
            if not self.is_valid_search_word(anchor):
                continue

            # Pokud již byla kotva otestována dříve, použijeme její známé skóre bez plýtvání dotazy
            if anchor in known_scores:
                score = known_scores[anchor]
                anchor_scores[anchor] = score
            else:
                score = self.submit_guess(anchor, enforce_valid=True)
                if score is not None:
                    anchor_scores[anchor] = score
                    known_scores[anchor] = score
                    yield {
                        "type": "guess",
                        "entry": self.guesses_history[-1],
                        "best": self.get_best_guess(),
                    }

            if self.is_won:
                yield {"type": "win", "word": self.winning_word, "total": len(self.guesses_history)}
                return

            # Dynamické předčasné ukončení Fáze 1 pouze při zásahu mimořádně horké specifické stopy (>= 88%)
            # Obecné hypernymy jako 'věc' nebo 'člověk' nesmí ukončit Fázi 1 předčasně!
            if score is not None and score >= 0.88 and anchor not in ["věc", "člověk"]:
                score_pct = round(score * 100, 2)
                yield {
                    "type": "strategy_pivot",
                    "trigger_word": anchor,
                    "score": score_pct,
                    "message": f"🔥 Mimořádně horká stopa: Kotva '{anchor}' dosáhla {score_pct}%! Přecházím k cílené triangulaci a vytěžování.",
                }
                break

        # 2. FÁZE: Rychlá triangulace a aktivace domén
        yield {"type": "phase", "phase": 2, "title": "Triangulace a aktivace sémantických domén"}
        domains = self.clusters.get("domains", {})
        cluster_priority: List[Tuple[str, float, Dict]] = []

        for c_key, c_info in domains.items():
            triggers = c_info.get("triggers", [])
            words_in_cluster = c_info.get("words", [])

            best_score = 0.0
            hot_count = 0

            for t in triggers:
                if t in known_scores:
                    if known_scores[t] > best_score:
                        best_score = known_scores[t]
                    if known_scores[t] >= 0.70:
                        hot_count += 1

            for cw in words_in_cluster:
                if cw in known_scores:
                    if known_scores[cw] > best_score:
                        best_score = known_scores[cw]
                    if known_scores[cw] >= 0.70:
                        hot_count += 1

            for a_word, a_doms in ANCHOR_DOMAINS_MAP.items():
                if c_key in a_doms and a_word in anchor_scores:
                    if anchor_scores[a_word] > best_score:
                        best_score = anchor_scores[a_word]
                    if anchor_scores[a_word] >= 0.70:
                        hot_count += 1

            # Priorita je dána nejlepším skóre + malý bonus za hustotu dalších úspěšných slov
            bonus = min(0.15, hot_count * 0.02)
            final_score = best_score + bonus if best_score > 0 else 0.0
            cluster_priority.append((c_key, final_score, c_info))

        cluster_priority.sort(key=lambda x: x[1], reverse=True)

        yield {
            "type": "clusters_ranked",
            "ranking": [
                {"name": c[2]["label"], "score": round(c[1] * 100, 2)} for c in cluster_priority[:5]
            ],
        }

        # Otestujeme prioritní spouštěče z top 5 domén pro triangulaci
        for c_key, c_score, c_info in cluster_priority[:5]:
            if self.is_won or len(self.guesses_history) >= target_limit:
                break
            for trg in c_info.get("triggers", [])[:3]:
                if self.is_won or len(self.guesses_history) >= target_limit:
                    break
                if trg in self.guessed_words or not self.is_valid_search_word(trg):
                    continue

                t_score = self.submit_guess(trg, enforce_valid=True)
                if t_score is not None:
                    known_scores[trg] = t_score
                    yield {
                        "type": "guess",
                        "entry": self.guesses_history[-1],
                        "best": self.get_best_guess(),
                    }
                    if self.is_won:
                        yield {"type": "win", "word": self.winning_word, "total": len(self.guesses_history)}
                        return
                    if t_score >= 0.82:
                        # Zásah horké stopy: okamžitě přecházíme do Fáze 3 pro hyper-zaměření
                        break

            # Pokud již máme maják >= 82%, neplýtváme pokusy na další domény
            if self.get_best_guess() and self.get_best_guess().get("raw_similarity", 0) >= 0.82:
                break

        # 3. FÁZE: Adaptivní sémantické stoupání a hyper-zaměření (Adaptive Hill-Climbing)
        yield {"type": "phase", "phase": 3, "title": "Adaptivní sémantické stoupání a hyper-zaměření"}

        last_notified_tier = 0
        consecutive_cold = 0

        while not self.is_won and len(self.guesses_history) < target_limit:
            # Prevence proti zacyklení ve slepé uličce fallbacku
            if consecutive_cold >= 10:
                yield {
                    "type": "strategy_pivot",
                    "trigger_word": "slepá ulička",
                    "score": 0,
                    "message": "Detekována série 10 ledových pokusů v řadě z Fallbacku. Zastavuji marné hádání.",
                }
                break

            top_best = self.get_best_guess()
            top_sim = top_best.get("raw_similarity", 0) if top_best else 0

            recs = self.get_candidate_recommendations(limit=30)
            
            best_known = [g["word"] for g in self.guesses_history if g.get("raw_similarity", 0) >= 0.70]
            best_known.sort(key=lambda w: top_best.get("raw_similarity", 0) if top_best and w == top_best["word"] else 0, reverse=True)
            top_5 = best_known[:5]
            top_5_str = ",".join(top_5)

            # Agresivní optimalizace: Zavoláme AI jakmile Pálí (>=0.85) nebo pokud nám došly normální tipy (recs)
            # Voláme POUZE pokud je fronta AI tipů (ai_candidates) prázdná, abychom zamezili spamování API a chybám 503
            if not self.ai_candidates and (not recs or top_sim >= 0.85) and top_5 and top_5_str != self.ai_last_requested_words:
                yield {
                    "type": "strategy_pivot",
                    "trigger_word": top_5[0],
                    "score": top_sim,
                    "message": f"🔥 Pálí! Zrychluji pomocí sémantického AI API kolem tref: {', '.join(top_5)}..."
                }
                self.ai_candidates = self.get_ai_hints(top_5)
                self.ai_last_requested_words = top_5_str

            next_word = None
            is_from_fallback = False

            # Tipy od AI mají nyní nejvyšší prioritu
            if self.ai_candidates:
                next_word = self.ai_candidates.pop(0)
                is_from_fallback = False  # AI tipy nepočítáme do "mrazivé slepé uličky"
            elif recs:
                next_word = recs[0]
            else:
                # Fallback: slova z nejlépe hodnocených domén
                for _, _, c_info in cluster_priority:
                    for cw in c_info.get("words", []):
                        if cw not in self.guessed_words and self.is_valid_search_word(cw):
                            next_word = cw
                            is_from_fallback = True
                            break
                    if next_word:
                        break
                    if next_word:
                        break

            # Pokud ani domény nemají další slova, zvolíme ze slovníku
            if not next_word:
                for vw in self.vocab:
                    if vw not in self.guessed_words and self.is_valid_search_word(vw):
                        next_word = vw
                        is_from_fallback = True
                        break

            if not next_word:
                break

            score = self.submit_guess(next_word, enforce_valid=True)
            if score is None:
                continue

            if is_from_fallback and score < 0.30:
                consecutive_cold += 1
            else:
                consecutive_cold = 0

            known_scores[next_word] = score
            entry = self.guesses_history[-1]
            best = self.get_best_guess()

            yield {
                "type": "guess",
                "entry": entry,
                "best": best,
            }

            if self.is_won:
                yield {
                    "type": "win",
                    "word": self.winning_word,
                    "total": len(self.guesses_history),
                }
                return

            score_pct = entry["score_pct"]
            if score_pct >= 95.0 and last_notified_tier < 3:
                last_notified_tier = 3
                yield {
                    "type": "scorching",
                    "word": next_word,
                    "score": score_pct,
                    "message": f"🔥 PÁLÍ! Slovo '{next_word.upper()}' ({score_pct}%) je těsně u cíle! Testuji nejužší synonyma...",
                }
            elif score_pct >= 85.0 and last_notified_tier < 2:
                last_notified_tier = 2
                yield {
                    "type": "lockin",
                    "word": next_word,
                    "score": score_pct,
                    "message": f"💥 PŘIHOŘÍVÁ! Nalezen klíčový směr: '{next_word.upper()}' ({score_pct}%). Spouštím hyper-zaměření na tento koncept!",
                }
            elif score_pct >= 70.0 and last_notified_tier < 1:
                last_notified_tier = 1
                yield {
                    "type": "hotspot_found",
                    "word": next_word,
                    "score": score_pct,
                    "message": f"☀️ TEPLO: Slovo '{next_word.upper()}' ({score_pct}%) potvrdilo správnou sféru.",
                }

        if not self.is_won:
            yield {
                "type": "done_unsolved",
                "message": f"Dosažen limit {target_limit} pokusů.",
                "best": self.get_best_guess(),
            }

    def get_best_guess(self) -> Optional[Dict]:
        if not self.guesses_history:
            return None
        return max(self.guesses_history, key=lambda x: x["score_pct"])

    def get_ai_hints(self, best_words: List[str]) -> List[str]:
        if not best_words:
            return []
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = (
            "Hraji českou hru Přihořívá (hledám tajné slovo podle sémantické podobnosti). "
            f"Moje nejlepší dosavadní trefy (od nejlepší) jsou: {', '.join(best_words)}. "
            "Vrať mi 40 českých slov (základní tvary, podstatná jména nebo přídavná jména), která s těmito slovy co nejvíce sémanticky souvisí. "
            "Formát odpovědi MUSÍ BÝT POUZE textový seznam slov oddělených čárkou (např. jablko, hruška, banán), nic dalšího nepiš."
        )
        
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    resp_data = json.loads(response.read().decode('utf-8'))
                    text = resp_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
                    words = [w.strip().lower() for w in text.replace('.', '').split(',') if w.strip()]
                    return [w for w in words if self.is_valid_search_word(w) and w not in self.guessed_words]
            except Exception as e:
                print(f"Gemini API ERROR (attempt {attempt+1}): {e}", flush=True)
                if attempt < 2:
                    time.sleep(2)
                else:
                    return []
        return []
