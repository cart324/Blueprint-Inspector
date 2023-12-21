import discord
from discord.ext import commands
import json
import traceback
import time

old_part_error = False


def is_basic_avatar(avatar_url):
    if avatar_url is None:
        return "https://cdn.discordapp.com/attachments/681058514797461647/1064418671100956682/image.png"
    else:
        return avatar_url


def is_passed(pass_dict):
    passed = True
    for i in pass_dict.values():
        if i is False:
            passed = False
            break
    return passed


def print_log(is_succeed, is_guild, author_name):
    now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))

    if is_succeed:
        text = "Processing success"
    else:
        text = "An error occurred"

    add = ""
    if not is_guild:
        add = " (in DM)"

    print(now + text + ", user = " + author_name + add)


class Inspection(commands.Cog):
    def __init__(self, client):
        self.client = client

        with open("data/blocks.json", "r") as block_data:
            block_data = json.load(block_data)
            self.block_dict = block_data

        with open("data/ban.txt", "r") as ban_data:
            self.ban_list = []
            for i in ban_data.readlines():
                self.ban_list.append(i)

        with open("data/ordnance_dictionary.json", "r") as ordnance_data:
            ordnance_data = json.load(ordnance_data)
            self.ordnance_dict = ordnance_data

        with open("data/sponsor_dictionary.json", "r") as sponsor_data:
            sponsor_dict = json.load(sponsor_data)
            self.sponsor_dict = sponsor_dict

        now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
        print(now + "Data load complete")

    def check_sub_construct(self, sub_construct, item_dict, repair_block):

        def check_sub_sub_construct(sub_sub_construct, repair_block):
            sub_repair_count = 0
            for i in sub_sub_construct:     # 서브 컨스트럭트 오픈
                if len(i["SCs"]) != 0:  # 하위 서브 컨스트럭트 존재 확인
                    sub_repair_count = sub_repair_count + check_sub_sub_construct(i["SCs"], repair_block)   # 하위 세기

                sub_repair_count = sub_repair_count + i["BlockIds"].count(repair_block)     # 메인 세기
            return sub_repair_count

        def check_drone_sub_construct(drone_sub_construct, item_dict):
            sub_ordnance_count = 0
            sub_cell_count = 0
            for i in drone_sub_construct:   # 서브 컨스트럭트 오픈
                if len(i["SCs"]) != 0:  # 하위 서브 컨스트럭트 존재 확인
                    count_list = check_drone_sub_construct(i["SCs"], item_dict)     # 하위 세기
                    sub_ordnance_count = sub_ordnance_count + count_list[0]     # 하위 무장 점수 합산
                    sub_cell_count = sub_cell_count + count_list[1]     # 하위 셀 수 합산

                sub_ordnance_count = sub_ordnance_count + counting_ordnance(i["BlockIds"], item_dict)  # 메인 무장 점수 세기
                sub_cell_count = sub_cell_count + counting_cells(i["BlockIds"], item_dict)  # 메인 셀 수 세기
            return [sub_ordnance_count, sub_cell_count]

        def counting_ordnance(block_list, item_dict):
            count = 0
            for i in block_list:    # 블록 리스트 등록
                block_data = call_block(i, item_dict)   # 블록 정보 호출
                if block_data:
                    block_point = self.ordnance_dict.get(block_data["Name"])    # 무장 점수 호출
                    if block_point is not None:     # 무장 점수 합산
                        count = count + int(block_point)
            return count

        def counting_cells(block_list, item_dict):
            count = 0
            for i in block_list:  # 블록 리스트 등록
                block_data = call_block(i, item_dict)  # 블록 정보 호출
                if block_data:  # 블록 크기 합산
                    count = count + block_data["Cell"]
            return count

        def call_block(item, item_dict):
            item = item_dict.get(item)
            if item:
                return item
            else:  # 데이터에 없는 블록 발견시 보고
                global old_part_error
                old_part_error = True
                return None

        repair_count = int(0)
        drone_count = int(0)
        ordnance_count = int(0)
        max_drone_ordnance = int(0)
        min_firepower = int(2147483647)
        max_cell = int(0)

        for i in sub_construct:  # 서브 컨스트럭트 오픈

            if i["COL"] is None:  # 서브 컨스트럭트
                if len(i["SCs"]) != 0:  # 하위 서브 컨스트럭트 존재 확인
                    repair_count = repair_count + check_sub_sub_construct(i["SCs"], repair_block)   # 하위 세기

                repair_count = repair_count + i["BlockIds"].count(repair_block)  # 메인 세기

            else:  # 기체
                drone_count = drone_count + 1
                cell_count = 0
                drone_ordnance_count = 0
                firepower = i["CSI"][14]

                if len(i["SCs"]) != 0:  # 하위 서브 오브젝트 존재 확인
                    count_list = check_drone_sub_construct(i["SCs"], item_dict)     # 하위 세기
                    drone_ordnance_count = drone_ordnance_count + count_list[0]  # 하위 무장 점수 합산
                    cell_count = cell_count + count_list[1]  # 하위 셀 수 합산

                    drone_ordnance_count = drone_ordnance_count + counting_ordnance(i["BlockIds"], item_dict)  # 메인 무장 점수 세기
                    cell_count = cell_count + counting_cells(i["BlockIds"], item_dict)  # 메인 셀 수 세기

                if max_drone_ordnance < drone_ordnance_count:  # 가장 높은 무장 점수일 경우 기록
                    max_drone_ordnance = drone_ordnance_count

                if min_firepower > firepower:  # 가장 적은 파이어파워일 경우 기록
                    min_firepower = firepower

                if max_cell < cell_count:  # 가장 큰 셀 수일 경우 기록
                    max_cell = cell_count

                ordnance_count = ordnance_count + drone_ordnance_count  # 총 무장 점수 합산

        if min_firepower == 2147483647:  # 드론이 0개일 때
            min_firepower = int(0)

        return [repair_count, drone_count, ordnance_count, max_drone_ordnance, min_firepower, max_cell]

    def check(self, file, ship, sponsor):
        template1 = {
            'Block_pass': True,
            'Repair_pass': True,
            'Drone_pass': True,
            'Ordnance_pass': True,
            'Drone_ordnance_pass': True,
            'Firepower_pass': True,
            'Cell_pass': True
        }

        template2 = {
            'Block_list': [],
            'Repair_count': 0,
            'Drone_count': 0,
            'Ordnance_count': 0,
            'Max_drone_ordnance': 0,
            'Min_firepower': 0,
            'Max_cell': 0
        }

        craft = {
            "Pass": template1,
            "Count": template2,
            "Name": "",
            "Cost": 0,
            "Firepower": 0,
            "Is_cv": False
        }

        repair_block = 0
        repair_count = 0
        drone_count = 0
        ordnance_count = 0

        sponsor_limit = self.sponsor_dict[sponsor]

        craft["Name"] = file['Name']
        craft["Cost"] = file['SavedMaterialCost']
        craft["Firepower"] = file["Blueprint"]["CSI"][14]

        raw_item_dict = file['ItemDictionary']  # key:숫자, value:코드
        item_dict = {}
        for i in raw_item_dict.keys():  # 아이템 딕셔너리 번역 (코드 -> 정보)
            block_dict = self.block_dict.get(raw_item_dict[i])
            if block_dict:
                block_name = block_dict["Name"]
                block_size = block_dict["Cell"]
                item_dict[int(i)] = {"Name": block_name, "Cell": block_size}  # 정수형 키값 입력
                if block_name in self.ban_list:  # 밴 블록 발견시 기록
                    craft["Pass"]['Block_pass'] = False
                    craft["Count"]["Block_list"].append(block_name)
                if block_name == "Compact Repair Tentacle":  # 리페어 블록 번호 기록
                    repair_block = int(i)

        cv_class_list = ["CVN", "CV", "CVL", "CVA", "LHD"]
        if ship in cv_class_list:   # 항공모함
            craft["Is_cv"] = True

            if repair_block is not None:  # 리페어 블록 카운트
                repair_count = file["Blueprint"]["BlockIds"].count(repair_block)

            count_list = self.check_sub_construct(file["Blueprint"]["SCs"], item_dict, repair_block)  # 서브 컨스트럭트 확인
            repair_count = repair_count + count_list[0]
            drone_count = drone_count + count_list[1]
            ordnance_count = ordnance_count + count_list[2]
            max_ordnance = count_list[3]
            min_firepower = count_list[4]
            max_cell = count_list[5]

            craft["Count"]["Repair_count"] = repair_count
            if repair_count > sponsor_limit[ship]["Repair"]:
                craft["Pass"]["Repair_pass"] = False

            craft["Count"]["Drone_count"] = drone_count
            if drone_count > sponsor_limit[ship]["Drone_max"]:
                craft["Pass"]["Drone_pass"] = False
            if drone_count < sponsor_limit[ship]["Drone_min"]:
                craft["Pass"]["Drone_pass"] = False

            craft["Count"]["Ordnance_count"] = ordnance_count
            if ordnance_count > sponsor_limit[ship]["Ordnance"]:
                craft["Pass"]["Ordnance_pass"] = False

            craft["Count"]["Max_drone_ordnance"] = max_ordnance
            if max_ordnance > 16:
                craft["Pass"]["Drone_ordnance_pass"] = False

            craft["Count"]["Min_firepower"] = min_firepower
            if min_firepower < 10:
                craft["Pass"]["Firepower_pass"] = False

            craft["Count"]["Max_cell"] = max_cell
            if max_cell > sponsor_limit[ship]["Cell"]:
                craft["Pass"]["Cell_pass"] = False

        else:  # 일반 함선
            if repair_block != 0:
                craft["Pass"]["Block_pass"] = False
                craft["Count"]["Block_list"].append("Compact Repair Tentacle")

        return craft

    texts = [
        {"Title": "Forbidden Block",
         "Pass_key": "Block_pass",
         "Count_key": "Block_list",
         "Text": ""},

        {"Title": "Repair Block Count",
         "Pass_key": "Repair_pass",
         "Count_key": "Repair_count",
         "Text": "Blocks"},

        {"Title": "Drone Count",
         "Pass_key": "Drone_pass",
         "Count_key": "Drone_count",
         "Text": "Drones"},

        {"Title": "Drone Ordnance Point",
         "Pass_key": "Ordnance_pass",
         "Count_key": "Ordnance_count",
         "Text": "Pts"},

        {"Title": "Drone with the most Ordnance Points usage",
         "Pass_key": "Drone_ordnance_pass",
         "Count_key": "Max_drone_ordnance",
         "Text": "Pts"},

        {"Title": "Weakest Drone's Firepower",
         "Pass_key": "Firepower_pass",
         "Count_key": "Min_firepower",
         "Text": ""},

        {"Title": "Biggest Drone's Cells",
         "Pass_key": "Cell_pass",
         "Count_key": "Max_cell",
         "Text": "Cells"}
    ]

    @commands.command(name="check")
    async def craft(self, ctx, *, sponsor="default"):
        author_avatar = is_basic_avatar(ctx.author.avatar)
        try:
            crafts = []
            ext_error = False
            for file in ctx.message.attachments:
                if str(file.filename).split(".")[-1] == "blueprint":
                    classification = str(file.filename).split("_")[0]

                    valid_class_list = ["CVN", "CV", "CVL", "DD", "FF", "FS", "FSL", "CVA", "CG", "LHD"]
                    if classification in valid_class_list:
                        file = await file.read()
                        file = file.decode("UTF-8")
                        file = json.loads(file)
                        crafts.append(self.check(file, classification, sponsor))  # 파일 검수

                    else:
                        class_pass = False
                        valid_class_list = ["CVN", "CV", "CVL", "FSL", "CVA", "CG", "LHD", "DD", "FF", "FS"]
                        file = await file.read()
                        file = file.decode("UTF-8")
                        file = json.loads(file)
                        for temp_class in valid_class_list:
                            temp_craft = self.check(file, temp_class, sponsor)  # 파일 검수
                            if is_passed(temp_craft["Pass"]):
                                temp_craft["Class"] = temp_class
                                crafts.append(temp_craft)
                                class_pass = True

                        if class_pass is False:
                            embed = discord.Embed(
                                title="ERROR",
                                description="OOPS, I can't find a classification for this.\nPlease check the file name.",
                                color=0xeb4258
                            )
                            embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                            embed.set_thumbnail(url=author_avatar)
                            embed.set_footer(text="Bug report : cart324")
                            await ctx.send(embed=embed)

                else:
                    ext_error = True
                    embed = discord.Embed(
                        title="ERROR",
                        description="OOPS, I can't read the file.\nPlease attach only `.blueprint` file",
                        color=0xeb4258
                    )
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    embed.set_footer(text="Bug report : cart324")
                    await ctx.send(embed=embed)

            if len(crafts) == 0:
                if ext_error:  # ext_error 로 인해 길이가 0이 될 수 있음
                    pass
                else:
                    embed = discord.Embed(
                        title="ERROR",
                        description="OOPS, The file is missing.\n"
                                    "Please attach `.blueprint`file when using this command.",
                        color=0xeb4258
                    )
                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    embed.set_footer(text="Bug report : cart324")
                    await ctx.send(embed=embed)

            else:
                for craft in crafts:
                    passed = is_passed(craft["Pass"])  # 패스 못한 항목 확인

                    if passed:  # 임배드 색깔 및 제목 지정
                        embed = discord.Embed(title=f"'{craft['Name']}' Results", color=0x00ff95)
                    else:
                        embed = discord.Embed(title=f"'{craft['Name']}' Results", color=0xeb4258)

                    embed.set_author(name=ctx.author.name, icon_url=author_avatar)
                    embed.set_thumbnail(url=author_avatar)
                    embed.add_field(name="Sponsor", value=sponsor, inline=False)
                    embed.add_field(name="Ship Cost", value=str(craft["Cost"]) + "Materials", inline=False)  # 함선 코스트
                    if craft["Is_cv"]:  # 서브 컨스트럭트 포함 파이어파워 (드론 합산)
                        embed.add_field(name="Ship Firepower with Drone", value=str(craft["Firepower"]), inline=False)
                    else:   # 서브 컨스트럭트 포함 파이어파워
                        embed.add_field(name="Ship Firepower", value=str(craft["Firepower"]), inline=False)

                    if craft.get("Class") is not None:
                        embed.add_field(name="guessed classification", value=craft["Class"], inline=False)

                    if craft["Is_cv"] is False:  # 일반 함선일 경우 리스트 변경
                        texts = [self.texts[0]]
                    else:
                        texts = self.texts

                    for text in texts:
                        text_passed = craft["Pass"][text["Pass_key"]]

                        if text_passed:
                            embed.add_field(
                                name=text["Title"],
                                value="🟢 " + str(craft["Count"][text["Count_key"]]) + text["Text"],
                                inline=False)
                        else:
                            embed.add_field(
                                name=text["Title"],
                                value="❌ " + str(craft["Count"][text["Count_key"]]) + text["Text"],
                                inline=False)

                    embed.set_footer(text="Bug report : cart324")
                    await ctx.send(embed=embed)
                    print_log(True, ctx.guild, ctx.author.name)

                if ctx.guild:
                    await ctx.message.delete()

                if old_part_error:
                    cart = self.client.get_user(344384179552780289)
                    await cart.send("```사용자 = " + ctx.author.name + "\n" + "파츠 갱신 필요```")

        except Exception:
            print_log(False, ctx.guild, ctx.author.name)
            embed = discord.Embed(title="ERROR", color=0xeb4258)
            embed.set_author(name=ctx.author.name, icon_url=author_avatar)
            embed.set_thumbnail(url=author_avatar)
            embed.add_field(name='This has been the worst bug in the history of bugs, maybe ever.',
                            value='​', inline=False)
            embed.add_field(name='Apply cold water to the bugged area.',
                            value="Achthually, you don't need to. The automatic report is on the way.",
                            inline=False)
            await ctx.send(embed=embed)
            error_log = traceback.format_exc(limit=None, chain=True)
            add = ""
            if not ctx.guild:
                add = " (in DM)"
            cart = self.client.get_user(344384179552780289)
            await cart.send("```사용자 = " + ctx.author.name + add + "\n" + str(error_log) + "```")


def setup(client):
    client.add_cog(Inspection(client))
