from enum import Enum, auto
from bs4 import BeautifulSoup
import requests
import os
import shutil
from datetime import datetime
import pyguetzli
from PIL import Image
import pysftp
from dotenv import load_dotenv
import re


class Soul(Enum):
    PALADIN = 1
    WARRIOR = 2
    DARK_KNIGHT = 3
    GUNBREAKER = 4
    WHITE_MAGE = 5
    SCHOLAR = 6
    ASTROLOGIAN = 7
    MONK = 8
    DRAGOON = 9
    NINJA = 10
    SAMURAI = 11
    BARD = 12
    MACHINIST = 13
    DANCER = 14
    BLACK_MAGE = 15
    SUMMONER = 16
    RED_MAGE = 17
    BLUE_MAGE = 18
    BOTANIST = 19
    FISHER = 20
    MINER = 21
    CULINARIAN = 22
    NULL = 0

    @staticmethod
    def find(isoul: str):
        for esoul in Soul:
            if (esoul.name.lower() == isoul.lower()):
                return esoul
        return Soul.NULL


class HLSoul:
    image: str = ''
    soul: Soul = Soul.NULL

    def __init__(self, image, soul):
        self.image = image
        self.soul = soul


HLSouls = [
    HLSoul("https://img.finalfantasyxiv.com/lds/h/x/B4Azydbn7Prubxt7OL9p1LZXZ0.png", Soul.FISHER),  # noqa
    HLSoul("https://img.finalfantasyxiv.com/lds/h/A/aM2Dd6Vo4HW_UGasK7tLuZ6fu4.png", Soul.MINER),  # noqa
    HLSoul("https://img.finalfantasyxiv.com/lds/h/A/aM2Dd6Vo4HW_UGasK7tLuZ6fu4.png", Soul.CULINARIAN),  # noqa
    HLSoul("https://img.finalfantasyxiv.com/lds/h/I/jGRnjIlwWridqM-mIPNew6bhHM.png", Soul.BOTANIST)  # noqa
]


class ProfileItem(Enum):
    WEAPON = 0
    SHIELD = 1
    HEAD = 2
    BODY = 3
    ARMS = 4
    WAIST = 5
    LEGS = 6
    FEET = 7
    EARRINGS = 8
    NECK = 9
    WRIST = 10
    RING1 = 11
    RING2 = 12
    SOUL = 13

    def find(self, iitem: str):
        for eitem in ProfileItem:
            if (eitem.name.lower() == iitem.lower()):
                return iitem
        return ""


class Updater():

    # Global Variables
    lodestone_url = os.getenv("LODESTONE_URL")
    iCount = 0
    iL = 0
    outputString = ""
    jsonOutputString = "{"
    ts = ""
    soulless = False
    currentSoul = Soul.NULL

    def gatherHTML(self):
        print("Requesting Lodestone...")
        req = requests.get(self.lodestone_url)
        soup = BeautifulSoup(req.text, "html.parser")
        return soup

    def parseHTML(self, soup: BeautifulSoup):
        print("Parsing Site...")

        print("Scraping Site...")

        soulString = ""

        try:
            soulSelect = soup.select('div[class*="icon-c--13"] h2')[0]
            soulSelect = soulSelect.contents[0]
            if ("Soul of the" in soulSelect):
                soulString = soulSelect[12:]
                self.currentSoul = Soul.find(soulString)
                print("Soul Found: " + soulString)
        except Exception:
            # If we made it here, the soul wasn't found automatically.
            # Revert to img scanning

            print("Unable to find soul...using fallback method.")
            self.soulless = True

            try:
                soulSelect = soup.select('div[class="character__class_icon"] img')[0]  # noqa
                soulSelect = soulSelect['src']

                # TODO: Add other icons, but I'll do this as necessary.
                foundSoul = [soul for soul in HLSouls if soul == soulSelect][0]

                if foundSoul is not None:
                    print("Found %s Icon" % soulSelect.soul.name.lower())
                    self.currentSoul = soulSelect.soul
                else:
                    print("Non-Soul class found but not hard-coded. Please validate:")  # noqa
                    print(soulSelect)
                    print("Exiting...")
                    exit()
            except Exception:
                print("Unable to find Soul...exiting.")
                exit()

        if not os.path.isdir("icons"):
            os.mkdir("icons")

        if not os.path.isdir("icons/" + self.currentSoul.name.lower()):
            os.mkdir("icons/" + self.currentSoul.name.lower())

        print("Deleting old icons if necessary...")
        path = os.path.normpath("icons/%s/" % self.currentSoul.name.lower())
        for file in os.listdir(path):
            imagepath = os.path.join(path, file)
            print("Deleting " + imagepath)
            os.remove(imagepath)
        print("Folder cleared.")

        # Profile Items
        for pi in ProfileItem:
            if (pi == ProfileItem.SHIELD and self.currentSoul != Soul.PALADIN):
                continue

            itemname = pi.name.lower()

            if (itemname != "soul" or (itemname == "soul" and self.soulless is False)):  # noqa
                itemcode = self.ProcessItem(self.currentSoul, soup, self.GetProfileItemString(pi), itemname)  # noqa
                self.jsonOutputString += ('"%s":"%s",') % (itemname, itemcode)
                self.outputString += ("Icon For %s:%s\r\n") % (itemname, itemcode)  # noqa
            else:
                print("Skipping soul because soulless")

        self.jsonOutputString += ('"iLevel":"%s",') % int(round((self.iL / self.iCount)))  # noqa

        # Attributes
        attribute_tables = soup.select(".character__param__list")
        attribute_pull_regex = "<tr><th.*><span.*>(.+)</span></th><td.*>(.+)</td></tr>"  # noqa
        p = re.compile(attribute_pull_regex, re.IGNORECASE)

        for attribute_table in attribute_tables:
            for content in attribute_table.contents:
                m = p.match(content.__str__())
                if m:
                    self.jsonOutputString += ('"%s":%s,') % (m.group(1).lower(), m.group(2))  # noqa

        self.jsonOutputString += ('"LastUpdated":"%s"') % (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()  # noqa

        self.jsonOutputString += "}"

        if not os.path.isdir("datafiles/"):
            os.mkdir("datafiles/")

        path = os.path.normpath("datafiles/" + self.currentSoul.name.lower() + "_itemids.json")  # noqa

        with open(path, "wb") as f:
            f.write(bytes(self.jsonOutputString, 'utf-8'))
        print("JSON Generation Complete")

        print("Starting File Compression...")

        path = os.path.normpath("icons/%s/" % self.currentSoul.name.lower())

        for file in os.listdir(path):
            imagepath = os.path.join(path, file)
            outputpath = os.path.join(path, file.replace(".png", ".jpg"))
            print("Optimizing " + file)
            if os.path.isfile(imagepath):
                image = Image.open(imagepath)
                optimized_image = pyguetzli.process_pil_image(image)
                with open(outputpath, "wb") as f:
                    f.write(optimized_image)
                if imagepath != outputpath:
                    print("Deleting " + imagepath)
                    os.remove(imagepath)

        print("File Compression Complete.")

        print("Beginning upload...")
        # TODO: This is a security "flaw"
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        with pysftp.Connection(
                os.getenv('SFTP_HOST'),
                username=os.getenv('SFTP_USER'),
                password=os.getenv('SFTP_PASS'),
                cnopts=cnopts) as sftp:
            print("Connection Established")
            with sftp.cd(os.getenv('BASE_PATH')):
                print("Checking for images folder...")
                try:
                    with sftp.cd('images'):
                        pass
                except IOError:
                    print("Images folder not found. Creating...")
                    sftp.mkdir('images')
                print("Uploading Images...")
                with sftp.cd('images'):
                    try:
                        with sftp.cd('%s' % self.currentSoul.name.lower()):
                            pass
                    except IOError:
                        sftp.mkdir('%s' % self.currentSoul.name.lower())
                    with sftp.cd('%s' % self.currentSoul.name.lower()):
                        for file in os.listdir(path):
                            imagepath = os.path.join(path, file)
                            if os.path.isfile(imagepath):
                                print("Uploading " + imagepath)
                                sftp.put(imagepath)
                try:
                    with sftp.cd('datafiles'):
                        pass
                except IOError:
                    sftp.mkdir('datafiles')
                with sftp.cd('datafiles'):
                    print("Uploading JSON")
                    jsonpath = os.path.normpath("datafiles/" + self.currentSoul.name.lower() + "_itemids.json")  # noqa
                    sftp.put(jsonpath)
        print("Upload Complete")

    def ProcessItem(self, currentSoul: Soul, soup: BeautifulSoup,
                    profileItemString: str, itemname: str):

        iconItems = soup.select(profileItemString)
        icon1Node = None
        for item in iconItems:
            if (item.has_attr('class') is False):
                icon1Node = item
                break

        icon1URL = str(icon1Node['href'])
        icon1URL = icon1URL[0:-1]
        icon1URL = icon1URL.replace("/?h1=", "")

        icon1Page = "http://na.finalfantasyxiv.com" + icon1URL
        icon1Code = icon1URL[icon1URL.rfind("/")+1:]

        iconPage = requests.get(icon1Page)
        soup2 = BeautifulSoup(iconPage.text, "html.parser")

        icon1ImageNode = soup2.select(".latest_patch__major__detail__item img")
        icon1ImageNode = icon1ImageNode[1]
        icon1ItemLevel = soup2.select(".db-view__item_level")[0]
        icon1ItemLevel = icon1ItemLevel.text

        if (itemname != "soul"):
            cIL: int = 0
            try:
                icon1ItemLevel = icon1ItemLevel.replace("Item Level ", "")
                cIL = int(icon1ItemLevel)
                self.iCount += 1
                self.iL += cIL
            except Exception:
                print("Error: Skipping Item: " + itemname)

        icon1ImageSrc = icon1ImageNode["src"]

        if not os.path.isdir("icons"):
            os.mkdir("icons")

        if not os.path.isdir("icons/" + self.currentSoul.name.lower()):
            os.mkdir("icons/" + self.currentSoul.name.lower())

        ending = icon1ImageSrc[:icon1ImageSrc.find("?")]
        ending = ending[ending.rfind("."):]
        path = os.path.normpath("icons/" + self.currentSoul.name.lower() + "/" + itemname + ending)  # noqa

        imgr = requests.get(icon1ImageSrc, stream=True)
        if (imgr.status_code == 200):
            with open(path, "wb") as f:
                f.raw.decode_content = True
                shutil.copyfileobj(imgr.raw, f)
                print("Downloaded (" + self.currentSoul.name + ") Icon For: " + itemname)  # noqa
        else:
            print("Image For " + itemname + " was non 200. Moving On...")

        return icon1Code

    def GetProfileItemString(self, item: ProfileItem):
        return 'div.icon-c--' + str(item.value) + '.ic_reflection_box.js__db_tooltip div a'  # noqa

    def main(self):
        print("Updater Started...")
        gathered_html = self.gatherHTML()
        self.parseHTML(gathered_html)
        print("Updater Finished!")


if __name__ == "__main__":
    updater: Updater = Updater()
    updater.main()
