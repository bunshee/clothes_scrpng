from pymongo import MongoClient

client = MongoClient("localhost", 27017)

DB = client["upwork"]

jobs = DB["jobs"]

jobs.insert_one(
    {
        "title": "Forex Trading Bot Developer Needed (ICT Strategies - MT4/MT5, TradingView, Python)",
        "url": "https://www.upwork.com/nx/search/jobs/</jobs/Forex-Trading-Bot-Developer-Needed-ICT-Strategies-MT4-MT5-TradingView-span-class-highlight-Python-span_~021891221552720489008/?referrer_url_path=/nx/search/jobs/>",
        "posted": "Posted 8 minutes ago",
        "budget": "Hourly: $20.00 - $40.00",
        "job_type": "Hourly",
        "experience_level": "Expert",
        "duration": "More than 6 months, Less than 30 hrs/week",
        "skills": [
            "Python",
            "Forex Trading",
            "MetaTrader 4",
            "C++",
            "MQL 4",
            "MetaTrader 5",
            "Derivatives Trading",
        ],
        "description": "We are seeking a skilled Forex Trading Bot Developer with expertise in ICT strategies for MT4/MT5 and TradingView, or proficiency in Python. The ideal candidate will have a strong understanding of algorithmic trading and be able to develop, test, and optimize high-performance trading bots. Your responsibilities will include coding strategies, backtesting performance, and providing ongoing support. If you have a proven track record in developing successful trading bots, we would love to hear from you!",
    }
)
