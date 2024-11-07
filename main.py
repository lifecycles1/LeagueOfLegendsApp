import tkinter as tk
from PIL import Image, ImageTk
import requests
import json
import os
import glob
import math
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from constants import HEADERS, ACCOUNT_URL, SUMMONER_URL, MATCH_IDS_URL, MATCH_INFO_URL, REGIONS, PLATFORMS, PROFILE_ICON_PATH, CHAMPION_ICON_PATH, CHAMPION_STRETCHED_ICON_PATH, ITEM_ICON_PATH, RUNE_NAME_PATH, STYLE1_TO_CATEGORY, RUNE_ICON_PATH


class LeagueOfLegendsApp(ttkb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("League of Legends App")
        self.geometry("1800x850")
        # Make root window stretchable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # frame manager for switching views
        self.frames = {}
        self.create_frames()
        # display main view (profile and match history)
        self.show_frame("MainView")
        self.center_window()

    def create_frames(self):
        """Creates all frames and stores them in the frames dictionary."""
        self.frames["MainView"] = MainView(self)
        self.frames["MatchDetailView"] = MatchDetailView(self)

    def show_frame(self, frame_name):
        """Brings a frame to the front."""
        frame = self.frames[frame_name]
        frame.grid(row=0, column=0, sticky="nsew")  # show the frame
        frame.tkraise()  # bring the frame to the front
        # self.update_idletasks()  # force layout update

    def center_window(self):
        self.update_idletasks()
        width = 1800
        height = 850

        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate the x and y coordinates to center the window
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Set geometry with calculated position
        self.geometry(f"{width}x{height}+{x}+{y}")


class MainView(ttkb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()
        self.current_row_index = 0

    def create_widgets(self):
        # input section
        input_frame = ttkb.Frame(self)
        input_frame.grid(row=0, column=0, columnspan=3, padx=20, pady=20)

        game_name_label = ttkb.Label(input_frame, text="Game Name:")
        game_name_label.grid(row=0, column=0)
        self.game_name_entry = ttkb.Entry(input_frame)
        self.game_name_entry.grid(row=0, column=1, padx=5, pady=5)

        tag_line_label = ttkb.Label(input_frame, text="Tag Line:")
        tag_line_label.grid(row=0, column=2)
        self.tag_line_entry = ttkb.Entry(input_frame)
        self.tag_line_entry.grid(row=0, column=3, padx=5, pady=5)

        self.region_var = tk.StringVar()
        region_dropdown = ttkb.Combobox(
            input_frame, textvariable=self.region_var, values=list(PLATFORMS.keys()), state="readonly")
        region_dropdown.set("Select a Region")
        region_dropdown.grid(row=0, column=4, padx=5, pady=5)

        search_button = ttkb.Button(
            input_frame, text="Search", command=self.on_search)
        search_button.grid(row=0, column=5, padx=5, pady=5)

        # profile section
        self.profile_frame = ttkb.Frame(
            self, height=226)
        self.profile_frame.grid_propagate(False)  # because of height
        self.profile_frame.grid(row=1, column=0, columnspan=2, padx=20,
                                pady=20, sticky=(N, S, E, W))
        self.profile_frame.grid_columnconfigure(0, weight=1)
        self.profile_frame.grid_rowconfigure(0, weight=1)
        profile_label = ttkb.Label(
            self.profile_frame, text="Profile Info will appear here", anchor="center")
        profile_label.grid(row=0, column=0, padx=10, pady=20)

        # match list section
        self.update_idletasks()
        input_frame_height = input_frame.winfo_height()
        profile_frame_height = self.profile_frame.winfo_height()
        parent_height = self.parent.winfo_height()
        total_padding = 120
        match_list_frame_height = parent_height - input_frame_height - \
            profile_frame_height - total_padding
        self.match_list_frame = ScrolledFrame(
            self, autohide=True, height=match_list_frame_height)
        self.match_list_frame.grid_propagate(False)
        self.match_list_frame.bind("<Configure>", self.on_scroll)

    def on_scroll(self, event: tk.Event) -> None:
        """Check if the user has scrolled to the bottom of the match list 
           and display a 'load more' button."""
        scroll_position = self.match_list_frame.vscroll.get()
        if scroll_position[0] > 0 and scroll_position[1] == 1.0:
            self.add_load_more_button()

    def add_load_more_button(self) -> None:
        """Add a button to load more matches."""
        ttkb.Button(self.match_list_frame, text="Load More", command=self.load_more_matches).grid(
            row=self.current_row_index, column=0, pady=20)

    def load_more_matches(self) -> None:
        """Load more matches when the user clicks the 'Load More' button."""
        new_match_ids = self.get_match_ids(
            self.puuid, self.region_base_url, self.current_row_index, 5)
        new_match_info = self.get_match_info(
            new_match_ids, self.region_base_url)
        self.display_match_history(new_match_info)

    def on_search(self) -> None:
        self.game_name = self.game_name_entry.get()
        tag_line = self.tag_line_entry.get()
        platform = self.region_var.get()
        start = 0
        count = 5

        if platform == "Select a Region":
            self.show_centered_messagebox("Please select a region.")
            return

        if platform in ["NA1", "LA1", "LA2", "BR1"]:
            self.region_base_url = REGIONS["AMERICAS"]
        elif platform in ["KR", "JP1"]:
            self.region_base_url = REGIONS["ASIA"]
        elif platform in ["EUW1", "EUN1", "TR1", "RU"]:
            self.region_base_url = REGIONS["EUROPE"]
        else:
            self.region_base_url = REGIONS["SEA"]

        # First API call to get the puuid
        self.puuid = self.get_puuid(
            self.game_name, tag_line, self.region_base_url)
        if self.puuid:
            # Second API call to get the summoner info
            summoner_info = self.get_summoner_info(
                self.puuid, PLATFORMS[platform])
            if summoner_info:
                self.display_profile_info(
                    summoner_info, self.game_name, tag_line)
                self.match_ids_list = self.get_match_ids(
                    self.puuid, self.region_base_url, start, count)
                self.match_info_list = self.get_match_info(
                    self.match_ids_list, self.region_base_url)
                self.display_match_history(self.match_info_list)
            else:
                self.display_profile_info(None, self.game_name, tag_line)

    def get_puuid(self, game_name: str, tag_line: str, region_base_url: str) -> str:
        """Get puuid for the given game name and tag line."""
        try:
            url = ACCOUNT_URL.format(
                base_url=region_base_url, game_name=game_name, tag_line=tag_line)
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            response_data = response.json()

            if "puuid" in response_data:
                return response_data["puuid"]
            else:
                raise ValueError(response_data.get(
                    "message", "Unknown error occurred."))
        except (requests.exceptions.HTTPError, ValueError) as e:
            self.handle_error(e, response)
            return ""
        except Exception as e:
            self.handle_error(e)
            return ""

    def get_summoner_info(self, puuid: str, platform_base_url: str) -> dict:
        """Get summoner info for the given puuid."""
        try:
            url = SUMMONER_URL.format(base_url=platform_base_url, puuid=puuid)
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            self.handle_error(e, response)
            return {}
        except Exception as e:
            self.handle_error(e)
            return {}

    def display_profile_info(self, summoner_info: dict, game_name: str, tag_line: str) -> None:
        """Display profile info in the profile frame."""
        # clear previous content in profile_frame
        for widget in self.profile_frame.winfo_children():
            widget.destroy()

        if summoner_info is None:
            profile_icon_id = "notfound"
            summoner_level = 0
        else:
            profile_icon_id = summoner_info["profileIconId"]
            summoner_level = summoner_info["summonerLevel"]

        # Load and display profile icon image
        if os.path.exists(os.path.join(PROFILE_ICON_PATH, f"{profile_icon_id}.png")):
            profile_icon_file = f"{profile_icon_id}.png"
        else:
            profile_icon_file = "notfound.png"
            self.show_centered_messagebox("Profile icon not found.")

        image = Image.open(os.path.join(
            PROFILE_ICON_PATH, profile_icon_file)).resize((100, 100), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        # Create label with profile picture
        profile_pic_label = ttkb.Label(
            self.profile_frame, image=photo, anchor="center")
        profile_pic_label.image = photo
        profile_pic_label.grid(row=0, column=0, padx=10, pady=10)

        # Display player level below the profile picture
        level_label = ttkb.Label(
            self.profile_frame, text=f"Level: {summoner_level}", anchor="center")
        level_label.grid(row=1, column=0, padx=10, pady=10)

        # Display the game name and tag line
        name_label = ttkb.Label(
            self.profile_frame, text=f"{game_name} #{tag_line}", font=("Arial", 12, "bold"), anchor="center")
        name_label.grid(row=2, column=0, padx=20, pady=10)

    def get_match_ids(self, puuid: str, region_base_url: str, start: int, count: int) -> list:
        """Get match ids for the given puuid."""
        try:
            url = MATCH_IDS_URL.format(
                base_url=region_base_url, puuid=puuid, start=start, count=count)
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            self.handle_error(e, response)
            return []
        except Exception as e:
            self.handle_error(e)
            return []

    def get_match_info(self, match_ids_list: list, region_base_url: str) -> dict:
        """Get match info for each match id in the list."""
        try:
            self.match_info_list = []
            for match_id in match_ids_list:
                url = MATCH_INFO_URL.format(
                    base_url=region_base_url, match_id=match_id)
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                response_data = response.json()
                self.match_info_list.append(response_data)
            return self.match_info_list
        except requests.exceptions.HTTPError as e:
            self.handle_error(e, response)
            return []
        except Exception as e:
            self.handle_error(e)
            return []

    def display_match_history(self, match_info_list: list) -> None:
        """Display match history in the match list frame."""
        self.match_list_frame.grid(
            row=2, column=0, columnspan=2, padx=20, pady=20, sticky=(N, S, E, W))

        for match_info in match_info_list:
            self.match_frame = ttkb.Frame(
                self.match_list_frame, borderwidth=2, relief="solid")
            self.match_frame.grid(row=self.current_row_index,
                                  column=0, padx=20)
            self.match_frame.bind("<Button-1>", lambda _,
                                  m=match_info: self.show_match_details(m))

            for participant in match_info['info']['participants']:
                if (participant['puuid'] == self.puuid):
                    self.display_match_row(
                        self.current_row_index, participant, match_info)
                    break

            self.current_row_index += 1

        # label to display loaded match count
        ttkb.Label(self, text=f"Loaded Matches: {self.current_row_index}").grid(
            row=2, column=0, columnspan=2, padx=(0, 60), sticky=(N, E))

    def show_match_details(self, match_info: dict) -> None:
        """Switch to MatchDetailView and pass teh match_id."""
        match_detail_view = self.parent.frames["MatchDetailView"]
        match_detail_view.display_match_details(
            self.game_name, match_info)
        self.parent.show_frame("MatchDetailView")

    def display_match_row(self, i: int, participant: dict, match_info: dict) -> None:
        """Display match row with participant details."""
        ### ROW VARS ###
        # CHAMP
        champ_name = participant['championName']
        champ_level = participant['champLevel']
        # RESULT - VICTORY/DEFEAT
        result = "VICTORY" if participant['win'] else "DEFEAT"
        result_color = "green" if result == "VICTORY" else "red"
        # GAME MODE - ARAM/NORMAL/RANKED, etc.
        game_mode = match_info['info']['gameMode']
        # STATS
        kda = f"{participant['kills']} / {participant['deaths']} / {participant['assists']}"
        minions_killed = participant['totalMinionsKilled']
        gold_earned = participant['goldEarned']

        self.display_champ_icon(i, champ_name)
        self.display_champ_level(i, champ_level)
        self.display_result(i, result, result_color)
        self.display_game_mode(i, game_mode)
        self.display_inventory(i, participant)
        self.display_stats(i, kda, minions_killed, gold_earned)

    def display_champ_icon(self, i: int, champ_name: str) -> None:
        """Display champion icon."""
        champ_pic_path = os.path.join(
            CHAMPION_ICON_PATH, f"{champ_name}.png")
        champ_image = Image.open(champ_pic_path).resize(
            (80, 80), Image.Resampling.LANCZOS)
        champ_photo = ImageTk.PhotoImage(champ_image)
        champ_label = ttkb.Label(
            self.match_frame, image=champ_photo)
        champ_label.image = champ_photo
        champ_label.grid(row=i, column=0, padx=20, pady=(25, 0))

    def display_champ_level(self, i: int, champ_level: int) -> None:
        """Display champion level."""
        ttkb.Label(self.match_frame, text=champ_level, font=(
            "Arial", 8), style=INVERSE).grid(row=i, column=0, sticky=(S))

    def display_result(self, i: int, result: str, result_color: str) -> None:
        """Display match result."""
        ttkb.Label(self.match_frame, text=result, font=("Arial", 8), foreground=result_color).grid(
            row=i, column=1, padx=(20, 40))

    def display_game_mode(self, i: int, game_mode: str) -> None:
        """Display game mode."""
        ttkb.Label(self.match_frame, text=game_mode, font=("Arial", 8)).grid(
            row=i, column=1, padx=(20, 40), sticky=(S), pady=(0, 15))

    def display_inventory(self, i: int, participant: dict) -> None:
        """Display inventory items."""
        inventory_frame = ttkb.Frame(self.match_frame)
        inventory_frame.grid(row=i, column=2, columnspan=7)
        for idx in range(7):
            item_pic_path = os.path.join(
                ITEM_ICON_PATH, f"{participant[f'item{idx}']}.png")
            item_image = Image.open(item_pic_path).resize(
                (40, 40), Image.Resampling.LANCZOS)
            item_photo = ImageTk.PhotoImage(item_image)
            item_label = ttkb.Label(
                inventory_frame, image=item_photo)
            item_label.image = item_photo
            padx_value = (0, 20) if idx == 6 else 0
            item_label.grid(row=i, column=idx, padx=padx_value)

    def display_stats(self, i: int, kda: str, minions_killed: int, gold_earned: int) -> None:
        """Display KDA, damage, gold, and minion stats."""
        ttkb.Label(self.match_frame, text=kda).grid(
            row=i+1, column=2, padx=(0, 10))
        ttkb.Label(self.match_frame, text=f"CS: {minions_killed}").grid(
            row=i+1, column=3, padx=(10, 10))
        ttkb.Label(self.match_frame, text=f"Gold: {gold_earned}").grid(
            row=i+1, column=4, padx=(20, 0))

    def display_masteries(self):
        """Display masteries section."""
        pass

    def show_centered_messagebox(self, message: str) -> None:
        """Display a centered messagebox window with the given message."""
        messagebox_window = ttkb.Toplevel(self)
        messagebox_window.overrideredirect(True)

        border_width = 2
        frame = ttkb.Frame(messagebox_window, borderwidth=border_width,
                           relief="solid", width=300, height=150)
        frame.grid_propagate(False)
        frame.grid(row=0, column=0, sticky="nsew")

        message_label = ttkb.Label(frame, text=message)
        message_label.grid(row=0, column=0, padx=10, pady=10)

        ok_button = ttkb.Button(
            frame, text="OK", command=messagebox_window.destroy, style="light")
        ok_button.grid(row=1, column=0, pady=10)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        messagebox_window.grab_set()
        self.update_idletasks()

        def center_messagebox():
            """Center the messagebox window on the parent window."""
            msgbox_width = messagebox_window.winfo_reqwidth()
            msgbox_height = messagebox_window.winfo_reqheight()
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (msgbox_width // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (msgbox_height // 2)
            messagebox_window.geometry(
                f"{msgbox_width}x{msgbox_height}+{x}+{y}")

        center_messagebox()

        def update_on_parent_move(event):
            """Update messagebox position when parent window moves."""
            if messagebox_window.winfo_exists():
                center_messagebox()

        self.master.bind("<Configure>", update_on_parent_move)
        messagebox_window.protocol(
            "WM_DELETE_WINDOW", lambda: self.master.unbind("<Configure>"))
        ok_button.config(command=lambda: (
            messagebox_window.destroy(), self.master.unbind("<Configure>")))

    def handle_error(self, error, response=None) -> None:
        """Handle and display error messages."""
        if isinstance(error, requests.exceptions.HTTPError) and response is not None:
            error_message = f"{response.status_code}: {response.reason}"
        else:
            error_message = str(error) or "An unexpected error occurred."

        self.show_centered_messagebox(error_message)


class MatchDetailView(ttkb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.style = ttkb.Style()

    def display_match_details(self, game_name: str, match_info: dict) -> None:
        """Update the UI with match details."""
        self.clear_content()
        self.configure_grid()

        self.game_name = game_name

        game_mode = match_info['info']['gameMode']
        game_duration = match_info['info']['gameDuration']
        game_end_timestamp = match_info['info'].get('gameEndTimestamp')

        self.display_header_row(game_mode, game_duration, game_end_timestamp)
        self.display_participants(match_info)

    def clear_content(self) -> None:
        """Clear the previous content of the frame."""
        for widget in self.winfo_children():
            widget.destroy()

    def configure_grid(self) -> None:
        """Configure grid layout for the frame."""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

    def display_header_row(self, game_mode: str, game_duration: int, game_end_timestamp: int) -> None:
        """Display header row on first row."""
        self.display_navigation_buttons()
        self.display_stats_icons()
        self.display_game_details(game_mode, game_duration, game_end_timestamp)

    def display_navigation_buttons(self) -> None:
        """Display navigation buttons on first row."""
        ttkb.Button(self, text="←", command=self.go_back).grid(
            row=0, column=0, padx=5, pady=5)
        ttkb.Button(self, text="X", command=self.go_main_view).grid(
            row=0, column=2, padx=5, pady=5)

    def go_back(self) -> None:
        """Navigate back to the match list."""
        self.parent.show_frame("MainView")

    def go_main_view(self) -> None:
        """Navigate back to the main profile view (initial view)."""
        self.parent.show_frame("MainView")

    def display_stats_icons(self) -> None:
        '''Display KDA, damage, and other stat icons on first row.'''
        # key = icon path, value = icon size
        icon_data = {
            "stats_icons/Untitled.png": (35, 35),
            "stats_icons/Untitled1.png": (35, 35),
            "stats_icons/Untitled2.png": (30, 30),
            "stats_icons/Untitled3.png": (30, 30),
            "stats_icons/Untitled4.png": (35, 35),
        }
        icon_positions = [475, 780, 1075, 1325, 1525]

        for (path, size), pos in zip(icon_data.items(), icon_positions):
            self.add_icon(path, size, pos)

    def add_icon(self, path: str, size: tuple, pos: int) -> None:
        """Add an icon to the frame."""
        icon = Image.open(path).resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(icon)
        label = ttkb.Label(self, image=photo)
        label.image = photo
        label.grid(row=0, column=1, padx=(pos, 0))

    def display_game_details(self, game_mode: str, game_duration: int, game_end_timestamp: int) -> None:
        """Display game details on first row."""
        ttkb.Label(self, text=game_mode, font=("Arial", 8)).grid(
            row=0, column=1, padx=(40, 0), sticky=(W))

        self.game_duration_minutes = self.get_game_duration_minutes(
            game_duration, game_end_timestamp)
        ttkb.Label(self, text=f"{self.game_duration_minutes:.0f} min", font=("Arial", 8)).grid(
            row=0, column=1, padx=(200, 0), sticky=(W))

    def get_game_duration_minutes(self, game_duration: int, game_end_timestamp: int) -> float:
        """Calculate the game duration in minutes."""
        if game_end_timestamp:
            return game_duration / 60  # gameDuration is in seconds
        else:
            return game_duration / 60000  # gameDuration is in milliseconds

    def display_participants(self, match_info: dict) -> None:
        """Display participant details."""
        participants = match_info['info']['participants']
        self.max_damage_dealt = max(p['totalDamageDealtToChampions']
                                    for p in participants)
        self.max_damage_taken = max(p['totalDamageTaken']
                                    for p in participants)

        for i, participant in enumerate(participants):
            self.display_participant_row(i, participant)

    def display_participant_row(self, i: int, participant: dict) -> None:
        """Display participant details in a row."""
        self.player_frame = ttkb.Frame(self, borderwidth=2, relief="solid")
        self.player_frame.grid(row=i+1, column=1, padx=20)
        self.player_frame.grid_columnconfigure(2, minsize=250)

        ### ROW VARS ####
        # CHAMP
        champ_level = participant['champLevel']
        champ_name = participant['championName']
        # PARTICIPANT GAME NAME
        participant_game_name = participant['riotIdGameName']
        # RUNE STYLES VARS
        style1 = participant['perks']['styles'][0]['selections'][0]['perk']
        style2 = participant['perks']['styles'][1]['style']
        # INVENTORY
        # note: inventory passes through the whole participant dict since item paths are constructed inside loop
        # STATS
        kda = f"{participant['kills']} / {participant['deaths']} / {participant['assists']}"
        kda1 = f"{participant['challenges']['kda']:0.1f} KDA"
        damage_dealt = participant['totalDamageDealtToChampions']
        damage_taken = participant['totalDamageTaken']
        gold_earned = f"{participant['goldEarned']:,}"
        gold_per_minute = math.ceil(
            participant['challenges']['goldPerMinute'])
        minions_killed = participant['totalMinionsKilled']

        # ASK - Is it better to pass participant:dict to each function or
        # declare vars outside and pass them in, especially for the function with lots of params
        self.display_champ_level(i, champ_level)
        self.display_champ_icon(i, champ_name)
        self.display_game_name_champ(i, participant_game_name, champ_name)
        self.display_rune_styles(i, style1, style2)
        self.display_inventory(i, participant)
        self.display_stats(i, kda, kda1, damage_dealt, damage_taken, gold_earned, gold_per_minute,
                           minions_killed, participant_game_name)

    def display_champ_level(self, i: int, champ_level: int) -> None:
        """Display champion level."""
        ttkb.Label(self.player_frame, text=champ_level, font=("Arial", 14)
                   ).grid(row=i, column=0, padx=(20, 0))

    def display_champ_icon(self, i: int, champ_name: str) -> None:
        """Display champion icon."""
        champ_pic_path = os.path.join(
            CHAMPION_STRETCHED_ICON_PATH, f"{champ_name}_0.jpg")
        champ_image = Image.open(champ_pic_path).resize(
            (200, 70), Image.Resampling.LANCZOS)
        champ_photo = ImageTk.PhotoImage(champ_image)
        champ_label = ttkb.Label(self.player_frame, image=champ_photo)
        champ_label.image = champ_photo
        champ_label.grid(row=i, column=1, padx=20)

    def display_game_name_champ(self, i: int, participant_game_name: str, champ_name: str):
        """Display game name and champion name."""
        self.style.configure(
            "SelfGameNameLabel.TLabel", foreground="#fabe0a")
        if participant_game_name == self.game_name:
            game_name_label = ttkb.Label(
                self.player_frame, text=f"{participant_game_name}\n{champ_name}", font=("Arial", 8, "bold"), style="SelfGameNameLabel.TLabel")
        else:
            game_name_label = ttkb.Label(
                self.player_frame, text=f"{participant_game_name}\n{champ_name}", font=("Arial", 8, "bold"))
        game_name_label.grid(row=i, column=2,  sticky=(W))

    def display_rune_styles(self, i: int, style1: int, style2: int) -> None:
        """Display rune styles."""
        with open(RUNE_NAME_PATH, "r") as f:
            runes_data = json.load(f)

        # Helper function to find style names
        def get_style_names(style1: int, style2: int) -> tuple:
            """Get style names from style ids."""
            style1_name, style2_name = None, None

            for obj in runes_data:
                if obj['id'] == style2:
                    style2_name = obj['key']

                for slot in obj['slots']:
                    for rune in slot['runes']:
                        if rune['id'] == style1:
                            style1_name = rune['key']
                            break

            return style1_name, style2_name

        style1_name, style2_name = get_style_names(style1, style2)

        # default values
        style1_name = style1_name or "0"
        style2_name = style2_name or "0"

        # process style1 image path
        style1_name = "VeteranAftershock" if style1_name == "Aftershock" else style1_name
        category = STYLE1_TO_CATEGORY.get(style1_name, "")

        if style1_name == "LethalTempo":
            style1_pic_path = os.path.join(
                RUNE_ICON_PATH, category, style1_name, f"{style1_name}Temp.png")
        else:
            style1_pic_path = os.path.join(
                RUNE_ICON_PATH, category, style1_name, f"{style1_name}.png")

        # process style2 image path
        style2_name = "Whimsy" if style2_name == "Inspiration" else style2_name
        style2_pic_path = glob.glob(os.path.join(
            RUNE_ICON_PATH, f"*{style2_name}.png"))[0]

        # load images
        style1_image = Image.open(style1_pic_path).resize(
            (35, 35), Image.Resampling.LANCZOS)
        style1_photo = ImageTk.PhotoImage(style1_image)

        style2_image = Image.open(style2_pic_path).resize(
            (25, 25), Image.Resampling.LANCZOS)
        style2_photo = ImageTk.PhotoImage(style2_image)

        # create canvas and display images
        canvas = ttkb.Canvas(self.player_frame, width=70,
                             height=70, highlightthickness=0)
        canvas.create_image(25, 25, image=style1_photo)
        canvas.create_image(40, 40, image=style2_photo)

        # store references to images
        canvas.style1_photo = style1_photo
        canvas.style2_photo = style2_photo
        canvas.grid(row=i, column=3)

    def display_inventory(self, i: int, participant: dict) -> None:
        """Display inventory items."""
        for idx in range(7):
            item_pic_path = os.path.join(
                ITEM_ICON_PATH, f"{participant[f'item{idx}']}.png")
            item_image = Image.open(item_pic_path).resize(
                (40, 40), Image.Resampling.LANCZOS)
            item_photo = ImageTk.PhotoImage(item_image)
            item_label = ttkb.Label(self.player_frame, image=item_photo)
            item_label.image = item_photo
            item_label.grid(row=i, column=4+idx)

    def display_stats(self, i: int, kda: str, kda1: str, damage_dealt: int, damage_taken: int, gold_earned: int, gold_per_minute: int, minions_killed: int, participant_game_name: str) -> None:
        """Display KDA, damage, gold, and minion stats."""
        def create_label(text: str, row: int, col: int, padx: tuple = (0, 0), pady: tuple = (0, 0), minsize: int = 100) -> ttkb.Label:
            """Helper to create and grid labels with standard settings."""
            self.player_frame.grid_columnconfigure(col, minsize=minsize)
            return ttkb.Label(self.player_frame, text=text, justify="center").grid(row=row, column=col, padx=padx, pady=pady)

        def create_progress_bar(value: float, row: int, col: int, style: str) -> ttkb.Progressbar:
            """Helper to create and grid progress bars with standard settings."""
            return ttkb.Progressbar(self.player_frame, length=100, value=value, mode="determinate", style=style).grid(row=row, column=col, pady=(30, 0))

        self.style.configure(
            "SelfDamageDealtBar.Horizontal.TProgressbar", background="#fabe0a", thickness=5)
        self.style.configure(
            "DamageDealtBar.Horizontal.TProgressbar", background="#cdfafa", thickness=5)
        self.style.configure(
            "DamageTakenBar.Horizontal.TProgressbar", background="#1f995c", thickness=5)

        # KDA display
        create_label(f"{kda}\n{kda1}", row=i, col=11,
                     padx=(50, 0), minsize=200)

        # Damage dealt display
        damage_dealt_text = f"★ {damage_dealt:,}" if damage_dealt == self.max_damage_dealt else f"{damage_dealt:,}"
        create_label(damage_dealt_text, row=i, col=12,
                     pady=(0, 20), minsize=150)
        damage_dealt_percent = (damage_dealt / self.max_damage_dealt) * 100
        damage_dealt_style = "SelfDamageDealtBar.Horizontal.TProgressbar" if participant_game_name == self.game_name else "DamageDealtBar.Horizontal.TProgressbar"
        create_progress_bar(damage_dealt_percent, row=i,
                            col=12, style=damage_dealt_style)

        # Damage taken display
        damage_taken_text = f"★ {damage_taken:,}" if damage_taken == self.max_damage_taken else f"{damage_taken:,}"
        create_label(damage_taken_text, row=i, col=13,
                     pady=(0, 20), minsize=150)
        damage_taken_percent = (damage_taken / self.max_damage_taken) * 100
        damage_taken_style = "SelfDamageDealtBar.Horizontal.TProgressbar" if participant_game_name == self.game_name else "DamageTakenBar.Horizontal.TProgressbar"
        create_progress_bar(damage_taken_percent, row=i,
                            col=13, style=damage_taken_style)

        # Gold earned display
        gold_text = f"{gold_earned}\n{gold_per_minute:,} / min"
        create_label(gold_text, row=i, col=14)

        # Minions killed display
        minions_per_minute = f"{minions_killed / self.game_duration_minutes:.1f}"
        minions_text = f"{minions_killed}\n{minions_per_minute} / min"
        create_label(minions_text, row=i, col=15)


if __name__ == "__main__":
    app = LeagueOfLegendsApp()
    app.mainloop()
