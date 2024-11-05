LOL_API_KEY = ""
HEADERS = {"X-Riot-Token": LOL_API_KEY}
ACCOUNT_URL = "https://{base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
SUMMONER_URL = "https://{base_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
MATCH_IDS_URL = "https://{base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
MATCH_INFO_URL = "https://{base_url}/lol/match/v5/matches/{match_id}"

REGIONS = {
    "AMERICAS": "americas.api.riotgames.com",  # NA1, LA1, LA2, BR1
    "ASIA": "asia.api.riotgames.com",  # KR, JP1
    "EUROPE": "europe.api.riotgames.com",  # EUW1, EUN1, TR1, RU,
    "SEA": "sea.api.riotgames.com"  # OC1, PH2, SG2, TH2, VN2, TW2
}

PLATFORMS = {
    "BR1": "br1.api.riotgames.com",
    "EUN1":	"eun1.api.riotgames.com",
    "EUW1":	"euw1.api.riotgames.com",
    "JP1": "jp1.api.riotgames.com",
    "KR": "kr.api.riotgames.com",
    "LA1": "la1.api.riotgames.com",
    "LA2": "la2.api.riotgames.com",
    "NA1": "na1.api.riotgames.com",
    "OC1": "oc1.api.riotgames.com",
    "TR1": "tr1.api.riotgames.com",
    "RU": "ru.api.riotgames.com",
    "PH2": "ph2.api.riotgames.com",
    "SG2": "sg2.api.riotgames.com",
    "TH2": "th2.api.riotgames.com",
    "TW2": "tw2.api.riotgames.com",
    "VN2": "vn2.api.riotgames.com"
}

__rune_categories = {
    "Domination": ["Electrocute", "DarkHarvest", "HailOfBlades"],
    "Precision": ["PressTheAttack", "LethalTempo", "FleetFootwork", "Conqueror"],
    "Sorcery": ["SummonAery", "ArcaneComet", "PhaseRush"],
    "Resolve": ["GraspOfTheUndying", "VeteranAftershock", "Guardian"],
    "Inspiration": ["GlacialAugment", "UnsealedSpellbook", "FirstStrike"]
}

STYLE1_TO_CATEGORY = {style: category for category,
                      styles in __rune_categories.items() for style in styles}

PROFILE_ICON_PATH = r"dragontail-14.20.1\14.20.1\img\profileicon"
CHAMPION_ICON_PATH = r"dragontail-14.20.1\14.20.1\img\champion"
ITEM_ICON_PATH = r"dragontail-14.20.1\14.20.1\img\item"
RUNE_NAME_PATH = r"dragontail-14.20.1\14.20.1\data\en_GB\runesReforged.json"
RUNE_ICON_PATH = r"dragontail-14.20.1\img\perk-images\Styles"
