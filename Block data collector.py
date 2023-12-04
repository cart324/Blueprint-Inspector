import os
import json

path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\From The Depths\\From_The_Depths_Data\\StreamingAssets\\Mods"


def read_files(target_path, target_ext, original_block_dict):
    def size_calculate(size_dict):
        size_positive = size_dict["SizePos"]
        size_negative = size_dict["SizeNeg"]
        size_x = 1 + int(size_positive["x"]) + int(size_negative["x"])
        size_y = 1 + int(size_positive["y"]) + int(size_negative["y"])
        size_z = 1 + int(size_positive["z"]) + int(size_negative["z"])
        cell = size_x * size_y * size_z
        return cell

    for (root, dirs, files) in os.walk(target_path):  # path 하위 폴더 전부 탐색
        for file in files:  # 개별 파일 입력
            ext = file.split(".")[-1]  # 확장자 추출
            if ext == target_ext:  # 확장자 확인
                with open(f"{root}\\{file}", 'r', encoding='UTF-8') as block_file:  # 파일 오픈
                    block_file = json.load(block_file)  # 파일 json 로드
                    block_id = block_file["ComponentId"]["Guid"]  # 블록 GUID 추출
                    block_name = block_file["ComponentId"]["Name"]  # 블록 인게임 이름 추출
                    if block_file["SizeInfo"] is None:  # 블록 사이즈 == 레퍼런스 블록 사이즈
                        original_block_id = block_file["IdToDuplicate"]["Reference"]["Guid"]    # 레퍼런스 블록 GUID 추출
                        block_cell = original_block_dict[original_block_id]["Cell"]     # 레퍼런스 블록 정보 호출
                    else:   # 블록 사이즈 != 레퍼런스 블록 사이즈
                        block_cell = size_calculate(block_file["SizeInfo"])  # 블록 볼륨 계산
                    block_dict[block_id] = {"Name": block_name, "Cell": block_cell}  # 블록 등록
            else:
                pass

    return block_dict


block_dict = {}
block_dict.update(read_files(path, "item", block_dict))
block_dict.update(read_files(path, "itemduplicateandmodify", block_dict))

with open("data/Blocks.json", "w") as block_dict_file:  # 저장 파일 오픈
    json.dump(block_dict, block_dict_file, indent="\t")  # 파일 작성
