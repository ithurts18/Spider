from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
STATE_DIR = BASE_DIR / "state"
PROFILE_DIR = STATE_DIR / "edge_profile"

DEFAULT_CITIES = {
    "北京": "101010100",
    "上海": "101020100",
    "深圳": "101280600",
}
DEFAULT_JOB_KEYWORDS = ["Python", "数据分析", "产品经理"]
DEFAULT_LIMIT_PER_CITY = 10
DEFAULT_OUTPUT_PATH = OUTPUT_DIR / "boss_jobs.xlsx"
DEFAULT_SHEET_NAME = "BossJobs"
SESSION_STATE_PATH = STATE_DIR / "boss_storage_state.json"
LOG_FILE_PATH = LOG_DIR / "boss_scraper.log"

BASE_URL = "https://www.zhipin.com"
HOME_URL = f"{BASE_URL}/"
LOGIN_URL = "https://login.zhipin.com/?ka=header-login"
SEARCH_URL = f"{BASE_URL}/web/geek/jobs"

EDGE_EXECUTABLE_PATH = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
DEBUG_PORT = 9222
DEBUG_ENDPOINT = f"http://127.0.0.1:{DEBUG_PORT}"

HEADLESS = False
PAGE_TIMEOUT_MS = 45_000
NAVIGATION_WAIT_UNTIL = "domcontentloaded"
MAX_PAGES_PER_QUERY = 5
MAX_RETRIES = 2
RANDOM_DELAY_RANGE = (0.8, 1.8)
NETWORK_IDLE_WAIT_MS = 2_500

EXCEL_COLUMNS = [
    "城市",
    "岗位名称",
    "薪资",
    "公司名",
    "学历要求",
    "工作经验",
    "技能关键词",
]

