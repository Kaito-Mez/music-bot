#really should add full integration with the text interface
import discord
from discord import Embed
import asyncio
import json

from discord import colour

#implement the multiple page system
#figure out how to update reactions faster/in parallel

class discordBook:
    def __init__(self, client, use_preset_reacts, json_path=None):
        self.client = client

        self.use_preset_reacts = use_preset_reacts
        self.preset_reacts = ['🗑','⬅','➡','➡']

        self.pages = {}
        self.reacts = {}

        #The message object once a page is sent

        #gonna be used for the multiple pages i think
        self.current_messages = {}
        self.message = None
        #index when creating pages
        self.pg_count = 0
        #Current displayed page on discord
        self.current_page = None
        
        self.data_file = json_path
        #set up all the initial pages
        if json_path != None:
            self.pages_from_json(json_path)

    '''back end, data manipulation stuff'''

    #called on __init__ and allows pages to be made using a csv file
    def pages_from_json(self, source):
        with open(source, encoding='utf8') as jsonfile:
            pages = json.load(jsonfile)
            for page in pages:
                self.new_page(
                page['title'],
                page['author'],
                page['description'],
                page['fields'],
                page['image'],
                page['video'],
                page['thumbnail'],
                page['footer'],
                page['timestamp'],
                page['url'],
                page['color'],
                page['reacts']
                )

    #appends an embed dictionary to the page dict
    def new_page(self, title, author, description, fields, image, video, thumbnail, footer, timestamp, url, color, reacts=[]):
        #data for making the embed
        self.embed_data = {
            #Compulsory data
            'title':title,
            'description':description,
            'author':author, 
            #must be a dictionary with entries in the format {inline_boolean:[entry_title, entry_text]}
            'fields':fields,
            
            #Non compulsory data
            #discord.Colour.from_rgb(color[0], color[1], color[2]).value
            'color':color,
            'image':image,
            'video':video,
            'thumbnail':thumbnail,
            'footer':footer,
            'timestamp':timestamp,
            'url':url,
            'reacts':reacts
            }
        
        self.pg_count += 1

        #adds the page to the dict
        self.pages.update({self.pg_count:self.embed_data})
        
        #Adds the reacts to the reacts dict
        react_list = []
        for i in reacts:
            react_list.append(i)
        self.reacts.update({self.pg_count:react_list})

    #Updates a value in the pages dictionary NOT TESTED YET
    def modify_page(self, page_num, permanent=False, **kwargs):
        #gets page dictionary
        modded_page = self.pages[page_num]
        #doesnt change a value if its not passed in kwargs

        for key in modded_page:
            if key == 'fields':
                modded_page[key] = []
                for item in kwargs.get(key, None):
                    modded_page[key].append(item)

                    #modded_page[key][kwargs.get(key, None).index(item)].update(item)
            else:
                modded_page.update({key:kwargs.get(key, modded_page[key])})
        
        #All of them done manually just in case the loop doesnt work, delete if it does
        '''modded_page.update({'title':kwargs.get('title', modded_page['title'])})
        modded_page.update({'description':kwargs.get('description', modded_page['description'])})
        modded_page.update({'fields':kwargs.get('fields', modded_page['fields'])})
        modded_page.update({'author':kwargs.get('author', modded_page['author'])})
        modded_page.update({'color':kwargs.get('color', modded_page['color'])})
        modded_page.update({'image':kwargs.get('image', modded_page['image'])})
        modded_page.update({'video':kwargs.get('video', modded_page['video'])})
        modded_page.update({'thumbnail':kwargs.get('thumbnail', modded_page['thumbnail'])})
        modded_page.update({'footer':kwargs.get('footer', modded_page['footer'])})
        modded_page.update({'timestamp':kwargs.get('timestamp', modded_page['timestamp'])})
        modded_page.update({'url':kwargs.get('url', modded_page['url'])})'''
        
        #sends the new data into the big page dict
        #self.pages[page_num].update({page_num:modded_page})

        if permanent:
            with open(self.data_file, 'w', encoding='utf8') as dumpfile:

                data = []
                pagenums = self.pages.keys()
                pagenums = sorted(pagenums)

                for i in pagenums:
                    data.append(self.pages[i])

                json.dump(data, dumpfile, indent=4)

    #removes a page from the dictionary NOT TESTED YET
    def remove_page(self, page_num):
        self.pages.pop(page_num)
        #consider settings this by using the length of the pages dict instead of a counter
        self.pg_count = self.pg_count-1
        for key in self.pages.keys():
            if int(key) > page_num:
                #theoretically ctrl x's the dictionary item 
                #and pastes it with the key being one less to fill the gap
                self.pages[int(key)-1] = self.pages.pop(key)

    '''user input responses that do stuff discord side'''

    #sends the message as well as storing it in self.message which is required for the other 
    #needs to be changed for the multi instance system
    async def send_book(self, channel):
        #fix this to ask for perms to delete other persons book
        if self.message != None:
            print('running this')
            await self.unsend_book()

        self.message = await channel.send(embed = Embed.from_dict(self.pages[1]))
        self.current_page = 1

        #uses ensure_future to resolve send_book before update finishes
        asyncio.ensure_future(self.update_reacts())

    #deletes message from discord and sets message to none
    async def unsend_book(self):
        if self.message != None:
            await self.message.delete()
            self.checking_for_react = False
            self.message = None
    
    #jumps to page
    async def change_page(self, page_num):
        try:
            await self.message.edit(embed= Embed.from_dict(self.pages[page_num]))
            self.current_page = page_num
            asyncio.ensure_future(self.update_reacts())

        except (AttributeError, discord.NotFound) as e:
            print(e)
            print('message has not been sent yet (change_page)')
    
    #loops back at the end
    async def cycle_page(self, cycle_dir):
        if cycle_dir == 'next':
            try:
                temp_page = self.current_page + 1
                #checks if its the last page so it can loop to 1st
                if temp_page > self.pg_count:
                    temp_page = 1
                
                await self.message.edit(embed= Embed.from_dict(self.pages[temp_page]))
                self.current_page = temp_page
                asyncio.ensure_future(self.update_reacts())

            except (AttributeError, discord.NotFound) as e:
                print(e)
                print('send_book not yet used (cycle_page)')

        elif cycle_dir == 'prev':
            try:
                #checks if 1st page so it can loop to last page
                temp_page = self.current_page - 1
                if temp_page < 1:
                    temp_page = self.pg_count

                await self.message.edit(embed= Embed.from_dict(self.pages[temp_page]))
                self.current_page = temp_page
                asyncio.ensure_future(self.update_reacts())

            except (AttributeError, discord.NotFound) as e:
                print(e)
                print('send_book not yet used (cycle_page (backwards))')

        else:
            print('wrong datatype given for cycle_type in cycle_page, should be str \'next\' or \'prev\'')
    
    #used to refresh the discord after a pages data has been changed
    async def update_page(self):
        try:
            await self.message.edit(embed=Embed.from_dict(self.pages[self.current_page]))
            asyncio.ensure_future(self.update_reacts())

        except (AttributeError, discord.NotFound) as e:
            print(e)
            print('message has not been sent (update_page)')
    
    #clears all un-needed reacts then repopulates
    async def update_reacts(self):
        try:
            #updates current reactions on the message
            async def get_current():
                cur_message = discord.utils.get(await self.message.channel.history(limit=10).flatten(), id = self.message.id)
                cur_reactions = cur_message.reactions
                return(cur_reactions)

            #cycles through all the current emotes and removes the unneeded ones
            for emoji in await get_current():
                if self.use_preset_reacts == True:
                    if str(emoji) not in self.reacts[self.current_page] and str(emoji) not in self.preset_reacts:
                        try:
                            await self.message.clear_reaction(emoji)
                        except discord.Forbidden:
                            await self.message.remove_reaction(emoji, self.client.user)

                elif str(emoji) not in self.reacts[self.current_page]:
                    try:
                        await self.message.clear_reaction(emoji)
                    except discord.Forbidden:
                        await self.message.remove_reaction(emoji, self.client.user)

            #updates the current right before it begins adding so it has a relevant list
            '''only checking once will probably negate most instances of the bot not adding the react because the users react is still there
            but still need to write something to fix that'''
            current_reacts = await get_current()

            #adds the default reacts
            '''gonna need to make it so that it checks whether the person that added it is the bot if reaction.me == True or soemthing'''
            if self.use_preset_reacts == True:
                for emoji in self.preset_reacts:
                    if str(emoji) not in current_reacts:
                        await self.message.add_reaction(emoji)

            
            #checks to see if the page has changed and if it has it stops adding emotes
            page_when_called = self.current_page

            for emoji in self.reacts[page_when_called]:
                if page_when_called == self.current_page:
                    if str(emoji) not in current_reacts:
                        await self.message.add_reaction(emoji)
                else:
                    print('page changed')
                    break

        except (AttributeError, discord.NotFound) as e:
            print(e)

    #needs to be called in a loop in order to get multiple responses
    #returns the index number of whatever react gets clicked
    async def handle_react(self, reaction, responder):
        
        def check(responder):
            #print(reaction.message, self.message)
            return(responder != self.client.user and reaction.message == self.message)

        if not check(responder):
            return -1
            
        print('responder is {}'.format(responder))

        user = responder

        #handles response after receiving it
        if self.use_preset_reacts == True:
            if str(reaction) in self.preset_reacts:
                
                if str(reaction.emoji) == '⬅':
                    try:
                        await self.message.remove_reaction(reaction, user)
                    except discord.Forbidden:
                        print('couldnt remove emote')
                    await self.cycle_page('prev')

                elif str(reaction) == '➡':
                    try:
                        await self.message.remove_reaction(reaction, user)
                    except discord.Forbidden:
                        print('couldnt remove emote')
                    await self.cycle_page('next')
                    
                elif str(reaction) == '🗑':
                    await self.unsend_book()
                    #returns 0 to signal that the loop should stop
                    print("GARBAGE")
                    return(0)

        #returns a value based on index of the emote in the relevant emote list
        if str(reaction) in self.reacts[self.current_page]:
            try:
                await self.message.remove_reaction(reaction, user)
            except discord.Forbidden:
                print('couldnt remove emote')

            #makes it so the 1st emote in the list returns 1 as 0 is reserved for deleting the page
            index = self.reacts[self.current_page].index(str(reaction))
            return(index+1)



#creating and populating a json file with python

if __name__ == "__main__":
    data = [{
        'reacts':['💢', '🗿'],
        'title':'testing',
        'description':'',
        'author':{'name':''},
        'fields':[['','',True],['','',False]],
        'image':{'url':None},
        'video':{'url':None},
        'thumbnail':{'url':'https://images-ext-2.discordapp.net/external/2ITLZXLv69CjihQwC1m9pyqIdKodM8i5ogKvPj2Vbfk/%3Fwidth%3D669%26height%3D671/https/images-ext-2.discordapp.net/external/raqJTvuQaf4RQC1J189TuTpRHVfnqbX285zyEoSWCQk/https/cdn.discordapp.com/attachments/366497342934745088/554176583120977921/SSEA_Logo.png?width=668&height=670'},
        'footer':{'text':''},
        'timestamp':None,
        'url':None,
        'color':[34, 171, 128]
        },
        {
        'reacts':['💢', '🗿'],
        'title':'',
        'description':'',
        'author':{'name':''},
        'fields':[['','',True],['','',False]],
        'image':{'url':None},
        'video':{'url':None},
        'thumbnail':{'url':'https://images-ext-2.discordapp.net/external/2ITLZXLv69CjihQwC1m9pyqIdKodM8i5ogKvPj2Vbfk/%3Fwidth%3D669%26height%3D671/https/images-ext-2.discordapp.net/external/raqJTvuQaf4RQC1J189TuTpRHVfnqbX285zyEoSWCQk/https/cdn.discordapp.com/attachments/366497342934745088/554176583120977921/SSEA_Logo.png?width=668&height=670'},
        'footer':{'text':''},
        'timestamp':None,
        'url':None,
        'color':[34, 171, 128]
        }]
    '''
    with open('data/screen.json', 'w', encoding='utf8') as testfile:
        #new =json.load(testfile)
        #print(new['entry']+1)
        json.dump(data, testfile, indent=4, ensure_ascii=False)'''