# Import
import json
import asyncio
import os
import requests
from discord import Webhook, Embed
from discord_webhook import DiscordWebhook, DiscordEmbed
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request, redirect, abort, jsonify, send_file
from flask_cors import CORS

# Init
app = Flask(__name__)
CORS(app)

# Variables
user_list = ip_list = read_list = {}


# Functions
def cf_turnstile_verify(response, remoteip):
    return json.loads(
        requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": os.environ["TURNSTILE_API_KEY"],
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
        username="Website - Spirax",
        avatar_url="https://spirax.me/assets/favicon/favicon-32x32.png",
):
    embed = DiscordEmbed(
        title=title,
        description=description,
        color=color,
    )
    webhook = DiscordWebhook(url=webhook_url, username=username, avatar_url=avatar_url)
    webhook.add_embed(embed)
    webhook.execute()

async def update_leaderboard(score: int, username: str, message_id: int):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(os.environ["LEADERBOARD_WEBHOOK_URL"], session=session)
        try:
            webhook_msg = await webhook.fetch_message(message_id)
            users = [x.split(". ")[1] for x in webhook_msg.embeds[0].fields[0].value.split("\n")]
            scores = [int(x) for x in webhook_msg.embeds[0].fields[1].value.split("\n")]
            if username in users:
                index = users.index(username)
                if int(scores[index]) < score:
                    scores[index] = score
            else:
                users.append(username)
                scores.append(score)
            users = [x for _, x in sorted(zip(scores, users), reverse=True)]
            scores = sorted(scores, reverse=True)
            users = [f"{i+1}. {x}" for i, x in enumerate(users)]
            if len(users) > 10:
                users.pop()
                scores.pop()
            newEmbed = Embed(title="**Stacker Leaderboard**", description="[**Click to Play!**](https://spirax.me/stacker)", color=0x3498DB)
            newEmbed.set_thumbnail(url="https://spirax.me/images/stack.webp")
            newEmbed.add_field(name="**Username**", value="\n".join(users), inline=True)
            newEmbed.add_field(name="**Score**", value="\n".join([str(x) for x in scores]), inline=True)
            newEmbed.set_footer(text="Last Updated")
            newEmbed.timestamp = datetime.now(tz=ZoneInfo('Asia/Kolkata'))
            await webhook.edit_message(message_id, embed=newEmbed)
        except Exception as e:
            if str(e) == "404 Not Found (error code: 10008): Unknown Message":
                newEmbed = Embed(title="**Stacker Leaderboard**", description="[**Click to Play!**](https://spirax.me/stacker)", color=0x3498DB)
                newEmbed.set_thumbnail(url="https://spirax.me/images/stack.webp")
                newEmbed.add_field(name="**Username**", value=f"1. {username}", inline=True)
                newEmbed.add_field(name="**Score**", value=score, inline=True)
                newEmbed.set_footer(text="Last Updated")
                newEmbed.timestamp = datetime.now(tz=ZoneInfo('Asia/Kolkata'))
                await webhook.send(embed=newEmbed, username="Stacker", avatar_url="https://spirax.me/images/favicon/favicon-32x32.png")
            else:
                print(e)

# Web Request Routes
@app.route("/", methods=["GET"])
def home():
    return redirect("https://spirax.me/", code=301)


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_file("media/favicon.ico")


@app.route("/v1/ping/", methods=["GET", "POST"])
def ping():
    return jsonify(message="200: Success")


@app.route("/v1/stacker/", methods=["POST"])
def stacker():
    username = request.json["username"].strip()
    score = request.json["score"]
    if username is not None and score is not None:
        if score == 0 or score > 99 or len(username) > 12 or len(username) < 3:
            return jsonify(message="200: Success")
        bw_flag = False
        badwords = ['ahole', 'anus', 'ash0le', 'ash0les', 'asholes', 'ass', 'Ass Monkey', 'Assface', 'assh0le', 'assh0lez', 'asshole', 'assholes', 'assholz', 'asswipe', 'azzhole', 'bassterds', 'bastard', 'bastards', 'bastardz', 'basterds', 'basterdz', 'Biatch', 'bitch', 'bitches', 'Blow Job', 'boffing', 'butthole', 'buttwipe', 'c0ck', 'c0cks', 'c0k', 'Carpet Muncher', 'cawk', 'cawks', 'Clit', 'cnts', 'cntz', 'cock', 'cockhead', 'cock-head', 'cocks', 'CockSucker', 'cock-sucker', 'crap', 'cum', 'cunt', 'cunts', 'cuntz', 'dick', 'dild0', 'dild0s', 'dildo', 'dildos', 'dilld0', 'dilld0s', 'dominatricks', 'dominatrics', 'dominatrix', 'dyke', 'enema', 'f u c k', 'f u c k e r', 'fag', 'fag1t', 'faget', 'fagg1t', 'faggit', 'faggot', 'fagit', 'fags', 'fagz', 'faig', 'faigs', 'fart', 'flipping the bird', 'fuck', 'fucker', 'fuckin', 'fucking', 'fucks', 'Fudge Packer', 'fuk', 'Fukah', 'Fuken', 'fuker', 'Fukin', 'Fukk', 'Fukkah', 'Fukken', 'Fukker', 'Fukkin', 'g00k', 'gay', 'gayboy', 'gaygirl', 'gays', 'gayz', 'God-damned', 'h00r', 'h0ar', 'h0re', 'hells', 'hoar', 'hoor', 'hoore', 'jackoff', 'jap', 'japs', 'jerk-off', 'jisim', 'jiss', 'jizm', 'jizz', 'knob', 'knobs', 'knobz', 'kunt', 'kunts', 'kuntz', 'Lesbian', 'Lezzian', 'Lipshits', 'Lipshitz', 'masochist', 'masokist', 'massterbait', 'masstrbait', 'masstrbate', 'masterbaiter', 'masterbate', 'masterbates', 'Motha Fucker', 'Motha Fuker', 'Motha Fukkah', 'Motha Fukker', 'Mother Fucker', 'Mother Fukah', 'Mother Fuker', 'Mother Fukkah', 'Mother Fukker', 'mother-fucker', 'Mutha Fucker', 'Mutha Fukah', 'Mutha Fuker', 'Mutha Fukkah', 'Mutha Fukker', 'n1gr', 'nastt', 'nigger;', 'nigur;', 'niiger;', 'niigr;', 'orafis', 'orgasim;', 'orgasm', 'orgasum', 'oriface', 'orifice', 'orifiss', 'packi', 'packie', 'packy', 'paki', 'pakie', 'paky', 'pecker', 'peeenus', 'peeenusss', 'peenus', 'peinus', 'pen1s', 'penas', 'penis', 'penis-breath', 'penus', 'penuus', 'Phuc', 'Phuck', 'Phuk', 'Phuker', 'Phukker', 'polac', 'polack', 'polak', 'Poonani', 'pr1c', 'pr1ck', 'pr1k', 'pusse', 'pussee', 'pussy', 'puuke', 'puuker', 'queer', 'queers', 'queerz', 'qweers', 'qweerz', 'qweir', 'recktum', 'rectum', 'retard', 'sadist', 'scank', 'schlong', 'screwing', 'semen', 'sex', 'sexy', 'Sh!t', 'sh1t', 'sh1ter', 'sh1ts', 'sh1tter', 'sh1tz', 'shit', 'shits', 'shitter', 'Shitty', 'Shity', 'shitz', 'Shyt', 'Shyte', 'Shytty', 'Shyty', 'skanck', 'skank', 'skankee', 'skankey', 'skanks', 'Skanky', 'slut', 'sluts', 'Slutty', 'slutz', 'son-of-a-bitch', 'tit', 'turd', 'va1jina', 'vag1na', 'vagiina', 'vagina', 'vaj1na', 'vajina', 'vullva', 'vulva', 'w0p', 'wh00r', 'wh0re', 'whore', 'xrated', 'xxx', 'b!+ch', 'bitch', 'blowjob', 'clit', 'arschloch', 'fuck', 'shit', 'ass', 'asshole', 'b!tch', 'b17ch', 'b1tch', 'bastard', 'bi+ch', 'boiolas', 'buceta', 'c0ck', 'cawk', 'chink', 'cipa', 'clits', 'cock', 'cum', 'cunt', 'dildo', 'dirsa', 'ejakulate', 'fatass', 'fcuk', 'fuk', 'fux0r', 'hoer', 'hore', 'jism', 'kawk', 'l3itch', 'l3i+ch', 'lesbian', 'masturbate', 'masterbat*', 'masterbat3', 'motherfucker', 's.o.b.', 'mofo', 'nazi', 'nigga', 'nigger', 'nutsack', 'phuck', 'pimpis', 'pusse', 'pussy', 'scrotum', 'sh!t', 'shemale', 'shi+', 'sh!+', 'slut', 'smut', 'teets', 'tits', 'boobs', 'b00bs', 'teez', 'testical', 'testicle', 'titt', 'w00se', 'jackoff', 'wank', 'whoar', 'whore', '*damn', '*dyke', '*fuck*', '*shit*', '@$$', 'amcik', 'andskota', 'arse*', 'assrammer', 'ayir', 'bi7ch', 'bitch*', 'bollock*', 'breasts', 'butt-pirate', 'cabron', 'cazzo', 'chraa', 'chuj', 'Cock*', 'cunt*', 'd4mn', 'daygo', 'dego', 'dick*', 'dike*', 'dupa', 'dziwka', 'ejackulate', 'Ekrem*', 'Ekto', 'enculer', 'faen', 'fag*', 'fanculo', 'fanny', 'feces', 'feg', 'Felcher', 'ficken', 'fitt*', 'Flikker', 'foreskin', 'Fotze', 'Fu(*', 'fuk*', 'futkretzn', 'gay', 'gook', 'guiena', 'h0r', 'h4x0r', 'hell', 'helvete', 'hoer*', 'honkey', 'Huevon', 'hui', 'injun', 'jizz', 'kanker*', 'kike', 'klootzak', 'kraut', 'knulle', 'kuk', 'kuksuger', 'Kurac', 'kurwa', 'kusi*', 'kyrpa*', 'lesbo', 'mamhoon', 'masturbat*', 'merd*', 'mibun', 'monkleigh', 'mouliewop', 'muie', 'mulkku', 'muschi', 'nazis', 'nepesaurio', 'nigger*', 'orospu', 'paska*', 'perse', 'picka', 'pierdol*', 'pillu*', 'pimmel', 'piss*', 'pizda', 'poontsee', 'poop', 'porn', 'p0rn', 'pr0n', 'preteen', 'pula', 'pule', 'puta', 'puto', 'qahbeh', 'queef*', 'rautenberg', 'schaffer', 'scheiss*', 'schlampe', 'schmuck', 'screw', 'sh!t*', 'sharmuta', 'sharmute', 'shipal', 'shiz', 'skribz', 'skurwysyn', 'sphencter', 'spic', 'spierdalaj', 'splooge', 'suka', 'b00b*', 'testicle*', 'titt*', 'twat', 'vittu', 'wank*', 'wetback*', 'wichser', 'wop*', 'yed', 'zabourah']
        for word in badwords:
            if word in username.lower():
                bw_flag = True
                break
        if bw_flag is False:
            asyncio.run(update_leaderboard(score, username, 1093232528959213608))
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
        webhook = DiscordWebhook(url=os.environ["DISCORD_WEBHOOK_STACKER_URL"], username="Website - Spirax",
                                 avatar_url="https://spirax.me/assets/favicon/favicon-32x32.png")
        webhook.add_embed(embed)
        webhook.execute()
        return jsonify(message="200: Success")
    else:
        abort(400)


@app.route("/v1/SubmitContactForm/", methods=["POST"])
def submitform():
    if cf_turnstile_verify(
            request.form["cf-turnstile-response"], request.headers.get("Cf-Connecting-Ip")
    ):
        email = request.form["email"]
        message = "```" + str(request.form["message"]) + "```"
        if message == "''''''":
            message = ""
        send_discord_webhook(
            os.environ["DISCORD_WEBHOOK_CONTACT_FORM_URL"],
            request.form["name"],
            f"**Email:**\n```{email}```\n**Message:**\n{message}",
        )
        return redirect(request.referrer)
    else:
        abort(403)
        

# Error Handlers
@app.errorhandler(400)
def bad_request():
    return redirect("https://spirax.me/400/", code=301)

@app.errorhandler(403)
def forbidden():
    return redirect("https://spirax.me/403/", code=301)
