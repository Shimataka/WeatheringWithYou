import configparser
import datetime
import json
import sys
from typing import Any, Dict, Optional
from urllib import parse, request

config_parser = configparser.ConfigParser()
config_parser.read("docs/config.ini", encoding="utf-8")

WEATHER_HACKS_URL: str = (
    "http://weather.livedoor.com/forecast/webservice/json/v1?city="
)
CITY_CODE: str = config_parser["PRIVATE"]["CITY_CODE"]
LOCATION_NAME: str = config_parser["PRIVATE"]["LOCATION_NAME"]

LINE_TOKEN: str = config_parser["PRIVATE"]["LINE_TOKEN"]
LINE_NOTIFY_URL: str = "https://notify-api.line.me/api/notify"

TODAY: int = 0


def get_weather_info() -> Dict[str, Any]:
    try:
        url: str = WEATHER_HACKS_URL + CITY_CODE
        html = request.urlopen(url)
        html_json: Dict[str, Any] = json.loads(html.read().decode("utf-8"))
    except Exception as e:
        print("Exception error : " + str(e))
        sys.exit(1)
    return html_json


def info_for_line(weather_json: Dict[str, Any], day: int) -> str:
    max_temperature: Optional[str] = None
    min_temperature: Optional[str] = None
    date: str = ""
    weather: str = ""
    try:
        date = weather_json["forecasts"][day]["date"]
        weather = weather_json["forecasts"][day]["telop"]
        max_temperature = weather_json["forecasts"][day]["temperature"]["max"][
            "celsius"
        ]
        min_temperature = weather_json["forecasts"][day]["temperature"]["min"][
            "celsius"
        ]
    except TypeError:
        pass

    msg: str = f"{date}  {LOCATION_NAME}の天気\n"
    msg += f"天気模様 : {weather}\n"
    msg += f"最高気温 : {max_temperature}℃\n"
    msg += f"最低気温 : {min_temperature}℃"
    return msg


def send_weather_info(msg: str) -> None:
    method: str = "POST"
    headers: Dict[str, str] = {"Authorization": "Bearer " + LINE_TOKEN}
    payload: Dict[str, str] = {"message": msg}
    try:
        payload_encoded: bytes = parse.urlencode(payload).encode("utf-8")
        req = request.Request(
            url=LINE_NOTIFY_URL,
            data=payload_encoded,
            method=method,
            headers=headers,
        )
        request.urlopen(req)
    except Exception as e:
        print("Exception error : " + str(e))
        sys.exit(1)


def Notify() -> None:
    weather_json: Dict[str, Any] = get_weather_info()

    if "雨" in weather_json["forecasts"][0]["telop"]:
        now: datetime.datetime = datetime.datetime.now() + datetime.timedelta(
            hours=9
        )  # GMT+9:00 "for AWS"
        weekday: int = now.weekday()
        yobi: list[str] = ["月", "火", "水", "木", "金", "土", "日"]
        msg_header: str = f"\n本日 {now.date()} ({yobi[weekday]})\n"

        msg: str = info_for_line(weather_json, TODAY + 1)
        send_weather_info(
            msg_header + "\n☔☔☔☔☔☔☔☔\n明日は雨が降ります\n\n" + msg
        )


if __name__ == "__main__":
    Notify()
