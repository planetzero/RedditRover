from core.BaseClass import Base
from os.path import dirname
from configparser import ConfigParser
import re


class SmallSubBot(Base):

    def __init__(self):
        super().__init__(None)
        super().factory_config()
        self.BOT_NAME = 'SmallSubBot'
        self.DESCRIPTION = self.config.get(self.BOT_NAME, 'description')
        self.USERNAME = self.config.get(self.BOT_NAME, 'username')
        self.OAUTH_FILENAME = self.config.get(self.BOT_NAME, 'oauth')
        self.REGEX = re.compile(r"\s(/?[rR]/[A-Za-z0-9][^\s\].,)]*)")
        self.DESCRIPTION_REGEX = re.compile(r"(\[).*?(\]\(.*?\))|(\\n)|(#)")  # Helps escaping shitty reddit markdown
        self.session, self.oauth = self.factory_reddit(config_file=dirname(__file__)+"/../config/"+self.OAUTH_FILENAME)
        self.responses = SmallSubText(dirname(__file__) + "/../config/bot_config.ini")
        self.banwords = ['x-post', 'xpost', 'crosspost', 'cross post', 'x/post',
                         'x\\post', 'via', 'from', 'hhh', 'trending subreddits']

    def execute_comment(self, comment):
        pass

    def execute_submission(self, submission):
        if any(bans in submission.title.lower() for bans in self.banwords): return False
        return self.general_action(submission)

    def execute_link(self, link_submission):
        if any(bans in link_submission.title.lower() for bans in self.banwords): return False
        return self.general_action(link_submission)

    def execute_titlepost(self, title_only):
        if any(bans in title_only.title.lower() for bans in self.banwords): return False
        return self.general_action(title_only)

    def update_procedure(self, thing_id, created, lifetime, last_updated, interval):
        pass

    def execute_textbody(self, textbody):
        self.oauth.refresh()
        result = self.REGEX.findall(" " + textbody)
        if result:
            response = self.generate_response(result, 'wtf')
            return response

    def general_action(self, submission):
        result = self.REGEX.findall(" " + submission.title)
        if result:
            self.oauth.refresh()
            response = self.generate_response(result, submission.subreddit.display_name)
            if response:
                self.session._add_comment(submission.name, response)
                return True
        return False

    def generate_response(self, subreddits, source_subreddit_name):
        subreddit_infos = []
        textbody = ""
        for subreddit in subreddits:
            sub_name = subreddit.split('r/')[-1].lower()
            if sub_name == source_subreddit_name.lower():
                continue

            already_found = False
            for dicts in subreddit_infos:
                if dicts['subreddit'] == sub_name:
                    already_found = True
                    break
            if already_found: continue

            target = self.session.get_subreddit(sub_name)
            if target.subscribers and target.subscribers < 10**5:
                description = self.DESCRIPTION_REGEX.sub('', target.description)
                description = self.description_formatter(description, target.over18)
                subreddit_infos.append({'subreddit': sub_name, 'description': description})

        if len(subreddit_infos) == 0: return
        for sub in subreddit_infos:
            textbody += self.responses.subreddit_binding.format(**sub)

        textbody = self.responses.intro + textbody + self.responses.outro
        return textbody.replace('\\n', '\n')

    @staticmethod
    def description_formatter(description, over18):
        """Formats a subreddit description"""
        nsfw = ('', '[**NSFW**]')[over18]
        # get the first line of their description
        for chars in description:
            if chars.isspace(): description = description[1:]
            else: break

        description = description.split('\n')[0]

        for x in range(10):
            if len(description) <= 250: break
            description = '.'.join(description.split('.')[:-1])

        if len(description) > 250:
            description = description[:250] + ' [...]'
        return description


class SmallSubText:
    intro = ""
    subreddit_binding = ""
    outro = ""

    def __init__(self, filepath):
        cp = ConfigParser()
        cp.read(filepath)
        self.intro = cp.get('SmallSubBot', 'intro')
        self.subreddit_binding = cp.get('SmallSubBot', 'subreddit_binding')
        self.outro = cp.get('SmallSubBot', 'outro')

    def __repr__(self):
        p = '\n\t'
        return "Fields:" + p + self.intro + p + self.subreddit_binding + p + self.outro


def init(database):
    """Init Call from module importer to return only the object itself, rather than the module."""
    return SmallSubBot()


if __name__ == "__main__":
    sst = SmallSubText(dirname(__file__) + "/../config/bot_config.ini")
    print(sst)
    ssb = SmallSubBot()
    print(ssb.execute_textbody("/r/dota2 r/dota2 r/bestof r/wtf r/dota2modding /r/dota2modding"))