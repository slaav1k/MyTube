import yadisk
import json
import SECRET


def list_video_files_with_links(token, path, video_extensions=(".mp4", ".mov", ".avi"),
                                cover_extensions=(".jpg", ".png"), indent=0, file_list=None):
    if file_list is None:
        file_list = []

    client = yadisk.Client(token=token)
    try:
        if not client.check_token():
            print("Ошибка: Токен недействителен")
            return file_list

        meta = client.get_meta(path)
        print("  " * indent + f"Папка: {meta.name}")

        # Ищем обложку в текущей папке
        cover_url = None
        for item in client.listdir(path):
            if item.type == "file" and item.name.lower().endswith(cover_extensions):
                try:
                    cover_url = client.get_download_link(item.path)
                    print("  " * (indent + 1) + f"Обложка найдена: {item.name} (прямая ссылка: {cover_url})")
                    break
                except yadisk.exceptions.YaDiskError as e:
                    print("  " * (indent + 1) + f"Ошибка получения ссылки на обложку: {e}")

        # Добавляем информацию о папке сериала с обложкой
        if indent == 1:  # Папка сериала (уровень после /mytube)
            file_list.append({
                "show_name": meta.name,
                "path": meta.path,
                "cover_url": cover_url,
                "seasons": []
            })

        for item in client.listdir(path):
            if item.type == "dir":
                print("  " * (indent + 1) + f"Папка: {item.name} (путь: {item.path})")
                # Рекурсивно обходим сезоны
                list_video_files_with_links(token, item.path, video_extensions, cover_extensions, indent + 1, file_list)
            else:
                if item.name.lower().endswith(video_extensions):
                    print("  " * (indent + 1) + f"Файл: {item.name} (путь: {item.path})")
                    try:
                        meta = client.get_meta(item.path)
                        public_url = meta.public_url
                        if not public_url:
                            client.publish(item.path)
                            meta = client.get_meta(item.path)
                            public_url = meta.public_url

                        if public_url:
                            mime_type = "video/mp4"  # Можно доработать для других форматов
                            video_info = {
                                "name": item.name,
                                "path": item.path,
                                "public_url": public_url,
                                "mime_type": mime_type
                            }
                            # Добавляем видео в сезон текущего сериала
                            if indent >= 2:  # Уровень сезона
                                for show in file_list:
                                    if show["path"].split("/")[2] == meta.path.split("/")[2]:
                                        show["seasons"].append({
                                            "season_name": meta.path.split("/")[3],
                                            "videos": [video_info]
                                        })
                            print("  " * (indent + 2) + f"Публичная ссылка: {public_url}")
                        else:
                            print("  " * (indent + 2) + f"Не удалось получить публичную ссылку")
                    except yadisk.exceptions.YaDiskError as e:
                        print("  " * (indent + 2) + f"Ошибка получения ссылки: {e}")
    except yadisk.exceptions.YaDiskError as e:
        print("  " * indent + f"Ошибка: {e}")
    finally:
        client.close()

    return file_list


def index_videos_to_file(token, path, output_file="videos.json"):
    files = list_video_files_with_links(token, path)

    # Сортируем и объединяем сезоны
    grouped_files = []
    for show in files:
        seasons = {}
        for season in show["seasons"]:
            season_name = season["season_name"]
            if season_name not in seasons:
                seasons[season_name] = []
            seasons[season_name].extend(season["videos"])
        show["seasons"] = [{"season_name": k, "videos": v} for k, v in seasons.items()]
        grouped_files.append(show)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grouped_files, f, ensure_ascii=False, indent=2)

    return grouped_files


if __name__ == '__main__':
    token = SECRET.TOKEN
    path = "/mytube"
    files = list_video_files_with_links(token, path)

    # Сортируем и объединяем сезоны для каждого сериала
    grouped_files = []
    for show in files:
        seasons = {}
        for season in show["seasons"]:
            season_name = season["season_name"]
            if season_name not in seasons:
                seasons[season_name] = []
            seasons[season_name].extend(season["videos"])
        show["seasons"] = [{"season_name": k, "videos": v} for k, v in seasons.items()]
        grouped_files.append(show)

    print("\nСписок всех сериалов с видео и обложками:")
    for show in grouped_files:
        print(f"Сериал: {show['show_name']} | Обложка: {show['cover_url']}")
        for season in show["seasons"]:
            print(f"  Сезон: {season['season_name']}")
            for video in season["videos"]:
                print(f"    Файл: {video['name']} | Ссылка: {video['public_url']}")

    with open("videos.json", "w", encoding="utf-8") as f:
        json.dump(grouped_files, f, ensure_ascii=False, indent=2)
