from dotenv import load_dotenv
import os
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)
from livekit.agents import function_tool
from hero_prompts import behavior_prompts, reply_prompts
from hero_search import search_internet, search_tool
from hero_weather_datetime import get_current_datetime, get_weather
#"""from hero_ctrl_system import(list_folder_items,
#                              run_application,
  #                            play_media_file,
   #                           get_battery_percentage,
    #                          open_settings,
     #                         get_system_info,
      #                        )"""
from hero_music import play_spotify_music
from hero_ctrl_system import (
    type_text,
    press_key,
    hotkey,
    move_mouse,
    click_mouse,
    scroll,
    read_screen,
    open_app,
    macro
)
load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=behavior_prompts,
                         tools= [search_internet, get_current_datetime, get_weather, search_tool,
                                 #create_folder,
                                 #list_folder_items,
                                 #run_application,
                                 #play_media_file,
                                 #get_battery_percentage,
                                 #open_settings,
                                 #get_system_info,
                                 play_spotify_music,
                                 type_text,
                                 press_key,
                                 hotkey,
                                 move_mouse,
                                 click_mouse,
                                 scroll,
                                 read_screen,
                                 open_app,
                                 macro]
                         )

async def entrypoint(ctx: agents.JobContext):
    try:
        session = AgentSession(
         llm=google.beta.realtime.RealtimeModel(
             voice="puck",  # Changed from "coral" to a valid voice kore,puck
             language="en-IN",
             api_key=os.getenv("GOOGLE_API_KEY")
         ),  
     )
     

        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

        await session.generate_reply(
            instructions=reply_prompts
        )
    except Exception as e:
        print(f"Error in entrypoint: {e}")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
