import interactions
import interactions as it
from interactions import Client, Button, ButtonStyle, SelectMenu, SelectOption, ActionRow, Modal, TextInput, TextStyleType, File
from interactions import CommandContext as CC
from interactions import ComponentContext as CPC
import datetime
from datetime import datetime
import time
import math
import asyncio
import aiohttp
import json
import psycopg2

class Ranking(interactions.Extension):
    skills = ['melee',
              'magic',
              'mining',
              'smithing',
              'woodcutting',
              'crafting',
              'fishing',
              'cooking',
              'tailoring'                 
             ]
    color_hex = {
                'melee': 0xff0000,
                'magic': 0x800080,
                'mining': 0x808080,
                'smithing': 0x800000,
                'woodcutting': 0x00ff00,
                'crafting': 0x808000,
                'fishing': 0x00ffff,
                'cooking': 0xff4500,
                'tailoring': 0xffffff,
                'total': 0x000000    
                }

    def __init__(self,client:Client) -> None:
        self.g_pager_reg = {}
        self.add_reg = {}
        return


    def get_tasks(self,session,skill_name:str):
        tasks = []
        for k in range(0,5000):  
            url='https://www.curseofaros.com/highscores-'
            tasks.append(asyncio.create_task(session.get(url+skill_name+'.json?p='+str(k))))
        return tasks
    
    
    async def search(self,skill_name:str) :
        """create a log with all guilds and their total xp in specific skill (top 100k in specified skill)"""
        skill_log = {} 
        #connector = aiohttp.TCPConnector(limit=80)
        async with aiohttp.ClientSession() as session :
            to_do = self.get_tasks(session, skill_name)
            responses = await asyncio.gather(*to_do)
            for response in responses:
                data = await response.json()
                if data != []:
                    for fdata in data :
                        player_name = fdata["name"]
                        tag = player_name.split()[0]
                        if len(tag) in range(2,6):
                            xp = fdata["xp"]
                            tag = tag.upper()
                            if tag in skill_log:
                                skill_log[tag] += xp 
                            else:
                                skill_log[tag] = xp
                elif data == []:
                    pass
        print("search "+skill_name+" done")
        return skill_log

    async def search_total(self) :
        """create a log with all guilds and their total xp (top 100k players in each skill)"""
        skills_log = {}
        _skill_log = {}
        _total_log = {}
        c_skill = ['melee','magic','mining', 'smithing', 'woodcutting', 'crafting', 'fishing', 'cooking','tailoring']
        for skill_x in range(9):
            #connector = aiohttp.TCPConnector(limit=80)
            async with aiohttp.ClientSession() as session :
                to_do = self.get_tasks(session, Ranking.skills[skill_x])
                responses = await asyncio.gather(*to_do)
                for response in responses:
                    data = await response.json()
                    if data != []:
                        for fdata in data :
                            player_name = fdata["name"]
                            tag = player_name.split()[0]
                            if len(tag) in range(2,6):
                                xp = fdata["xp"]
                                tag = tag.upper()
                                
                                if tag in _skill_log:
                                    _skill_log[tag] += xp 
                                else:
                                    _skill_log[tag] = xp
                                    
                                if tag in _total_log:
                                    _total_log[tag] += xp 
                                else:
                                    _total_log[tag] = xp 
                                    
                    elif data == []:
                        break
            skills_log[Ranking.skills[skill_x]]=_skill_log
            _skill_log.clear()
        skills_log["total"] = _total_log
        return skills_log

    def listify(self,entities_dict:dict) -> list:
        """convert {key,value} dict in 'key -- value' string"""
        entities_list = []
        for key, value in entities_dict.items():
            entity = key + " -- " + "{:,}".format(value) 
            entities_list.append(entity)
        return entities_list
        
    def order_dict(self,unordered_dict:dict) -> dict:
        """order a given dictionnary"""
        _ordered_dict = {k: v for k, v in sorted(unordered_dict.items(), key=lambda item: item[1],reverse=True)}
        return _ordered_dict
        
    def embed_maker(self,result:list,ranks:int,skill:str):
        """make guild ranking embed in specific skill with certain count"""
        fields_list = []
        for i in range(ranks):
            rank = i + 1
            field = it.EmbedField(name=f"Rank#{rank}", value=result[i])
            fields_list.append(field)
        ranking_embed = it.Embed(
                        title=f"Top {ranks} Guilds : {skill.capitalize()} ",
                        description="\u200b",       
                        fields=fields_list,
                        color=Ranking.color_hex[skill])
        
        return ranking_embed









    @interactions.extension_command(
                                    name='guilds',
                                    description="Show guilds ranking in a specific skill or total xp",
                                    options=[
                                            it.Option(
                                                name="skill",
                                                description="The Leaderboard Skill",
                                                type=it.OptionType.STRING,
                                                required=True,
                                                choices=[
                                                        it.Choice(name="Total",value="total"),
                                                        it.Choice(name="Melee",value="melee"),
                                                        it.Choice(name="Magic",value="magic"),
                                                        it.Choice(name="Mining",value="mining"),
                                                        it.Choice(name="Smithing",value="smithing"),
                                                        it.Choice(name="Woodcutting",value="woodcutting"),
                                                        it.Choice(name="Crafting",value="crafting"),              
                                                        it.Choice(name="Fishing",value="fishing"),
                                                        it.Choice(name="Cooking",value="cooking"),
                                                        it.Choice(name="Tailoring",value="tailoring")
                                                        ]
                                                    ),
                                            it.Option(
                                                name="ranks",
                                                description="How many guilds to show \nshould be in [1 - 25], default to 10",
                                                type=it.OptionType.INTEGER,
                                                min_value=1,
                                                max_value=25,
                                                required=False
                                                      )
                                            ],	
                                    scope=[957035929787322478]
                                    )
    async def guilds(self,ctx:CC,skill:str,ranks:int=10):
        await ctx.defer()
        await ctx.send(f"Fetching {skill.capitalize()} Xp ... ")
        results = []
        _ordered_results = {}
        
        if skill == "total":
            results0 = asyncio.run(self.search_total())
            results = results0["total"]
        else:
            results = asyncio.run(self.search(skill.lower()))
            
        _ordered_results = self.order_dict(results)
        _guilds_list = self.listify(_ordered_results)
        _embed = self.embed_maker(_guilds_list,int(ranks),skill)
                    
        await ctx.edit("Finished !",embeds=_embed)




def setup(client:Client):
    Ranking(client)
