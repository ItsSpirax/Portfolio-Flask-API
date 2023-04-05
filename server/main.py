# Import
import json
import os

import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from flask import Flask, request, redirect, abort, jsonify, send_file
from flask_cors import CORS

# Init
app = Flask(__name__)
CORS(app)

# Variables
user_list = ip_list = {}


# Functions
def captcha_verify(response, remoteip):
    return json.loads(
        requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": os.environ["RECAPTCHA_API_KEY"],
                "response": response,
                "remoteip": remoteip,
            },
        ).content
    )["success"]


def send_discord_webhook(
        webhook_url,
        title,
        description,
        color="39d874",
        username="Website - Adith",
        avatar_url="https://adith.ml/assets/favicon/favicon-32x32.png",
):
    embed = DiscordEmbed(
        title=title,
        description=description,
        color=color,
    )
    webhook = DiscordWebhook(url=webhook_url, username=username, avatar_url=avatar_url)
    webhook.add_embed(embed)
    webhook.execute()


# Web Request Routes
@app.route("/", methods=["GET"])
def home():
    return redirect("https://adith.ml", code=301)


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_file("media/favicon.ico")


@app.route("/v1/ping", methods=["GET", "POST"])
def ping():
    return jsonify(message="200: Success")


@app.route("/v1/stacker", methods=["POST"])
def stacker():
    username = request.json["username"]
    score = request.json["score"]
    if username == "Adith":
        score += 10
    if username is not None and score is not None:
        if score == 0 or score > 50:
            return jsonify(message="200: Success")
        adblock = str(request.json["adblock"])
        width = request.json["width"]
        height = request.json["height"]
        color = request.json["color"]
        rotation = "Portrait"
        if  request.json["rotation"] in ["landscape-primary", "landscape-secondary", "landscape"] :
            rotation = "Landscape"
        try:
            battery = f"\n\n**Battery:** {request.json['battery']}\n**Charging:** {str(request.json['charging'])}"
        except:
            battery = ""
        user_agent = str(request.headers.get("User-Agent"))
        if user_agent in user_list:
            response = user_list[user_agent]
        else:
            response = requests.post(
                "https://api.whatismybrowser.com/api/v2/user_agent_parse",
                data=json.dumps({"user_agent": f"{user_agent}"}),
                headers={"X-API-KEY": os.environ["WHAT_IS_MY_BROWSER_API_KEY"]},
            )
            user_list[user_agent] = response
        json_response = json.loads(response.content)
        platform = json_response["parse"]["simple_software_string"]
        model = f"\n**Model:** {json_response['parse']['simple_operating_platform_string']}"
        if json_response["parse"]["simple_operating_platform_string"] is None:
            model = ""
        ip = str(request.headers.get("Cf-Connecting-Ip"))
        if ip in ip_list:
            response = ip_list[ip]
        else:
            response = requests.get(
                f"https://ipgeolocation.abstractapi.com/v1/?api_key={os.environ['ABSTRACT_API_KEY']}&ip_address={ip}"
            )
            ip_list[ip] = response
        json_response = json.loads(response.content)
        ip_country_code = json_response["country_code"]
        ip_location = f"{json_response['city']}, {json_response['region']}"
        ip_postal_code = json_response["postal_code"]
        ip_currency = json_response["currency"]["currency_name"]
        ip_timezone = f"{json_response['timezone']['name']} ({json_response['timezone']['abbreviation']})"
        ip_is_vpn = json_response["security"]["is_vpn"]
        ip_connection_type = json_response["connection"]["connection_type"]
        ip_org = json_response["connection"]["autonomous_system_organization"]
        vpn = ""
        if str(ip_is_vpn).lower() == "true":
            vpn = " (VPN)"
        embed = DiscordEmbed(
            title=f"{username}   (Score: {score})",
            description=f"**Platform:** {platform}{model}\n\n**Display:** {width} x {height} ({color} bit)\n"
                        f"**Orientation:** {rotation}{battery}\n",
            color="39d874",
        )
        embed.set_thumbnail(
            url=f"https://flagcdn.com/h240/{ip_country_code.lower()}.png"
        )
        embed.add_embed_field(name="IP:", value=ip)
        embed.add_embed_field(name="Location:", value=ip_location)
        embed.add_embed_field(name="Postal Code:", value=ip_postal_code)
        embed.add_embed_field(name="Currency:", value=ip_currency)
        embed.add_embed_field(name="Time Zone:", value=ip_timezone)
        embed.add_embed_field(name="Adblocker Enabled:", value=adblock)
        embed.add_embed_field(
            name="Connection Type:", value=f"{ip_connection_type}{vpn}"
        )
        embed.add_embed_field(name="Organization:", value=ip_org)
        webhook = DiscordWebhook(url=os.environ["DISCORD_WEBHOOK_STACKER_URL"], username="Website - Adith",
                                 avatar_url="https://adith.ml/assets/favicon/favicon-32x32.png")
        webhook.add_embed(embed)
        webhook.execute()
        return jsonify(message="200: Success")
    else:
        abort(400)


@app.route("/v1/SubmitForm", methods=["POST"])
def submitform():
    if captcha_verify(
            request.json["g-recaptcha-response"], request.headers.get("X-Forwarded-For")
    ):
        email = request.json["email"]
        comment = "```" + str(request.json["comment"]) + "```"
        if comment == "''''''":
            comment = ""
        send_discord_webhook(
            os.environ["DISCORD_WEBHOOK_CONTACT_FORM_URL"],
            request.json["name"],
            f"**Email:**\n```{email}```\n**Message:**\n{comment}",
        )
        return jsonify(message="200: Success")
    else:
        abort(403)


# Error Handlers
@app.errorhandler(400)
def bad_request():
    return jsonify(error="400: Bad Request"), 400


@app.errorhandler(401)
def unauthorized():
    return jsonify(error="401: Unauthorized"), 401


@app.errorhandler(403)
def forbidden():
    return jsonify(error="403: Forbidden"), 403


@app.errorhandler(404)
def page_not_found():
    return jsonify(error="404: Not Found"), 404


@app.errorhandler(405)
def method_not_allowed():
    return jsonify(error="405: Method Not Allowed"), 405


@app.errorhandler(500)
def server_error():
    return jsonify(error="500: Server Error"), 500


@app.errorhandler(505)
def not_supported():
    return jsonify(error="505: HTTP Not Supported"), 505
