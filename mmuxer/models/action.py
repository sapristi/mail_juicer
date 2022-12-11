import logging
from abc import abstractmethod
from typing import Literal, Union

from imap_tools import BaseMailBox, MailMessage

from .common import BaseModel
from .enums import Flag

logger = logging.getLogger(__name__)


def format_message(msg: MailMessage):
    return f"[{{{msg.uid}}} {msg.from_} -> {msg.to} '{msg.subject}']"


class BaseAction(BaseModel):
    @abstractmethod
    def _apply(self, mailbox: BaseMailBox, message: MailMessage):
        pass

    @abstractmethod
    def format(self, message):
        pass

    def skip(self, message):
        return False

    def apply(self, mailbox: BaseMailBox, message: MailMessage, dry_run: bool):
        if self.skip(message):
            logger.debug("SKIP %s", self.format(message))
            return
        if dry_run:
            logger.info("%s [DRY_RUN]", self.format(message))
        else:
            logger.info(self.format(message))
            self._apply(mailbox, message)


class MoveAction(BaseAction):
    action: Literal["move"] = "move"
    dest: str

    def skip(self, message):
        return getattr(message, "associated_folder", None) == self.dest

    def _apply(self, mailbox: BaseMailBox, message: MailMessage):
        mailbox.move(message.uid, self.dest)

    def format(self, message):
        return f"MOVE {format_message(message)} --> {self.dest}"


class DeleteAction(BaseAction):
    action: Literal["delete"] = "delete"

    def _apply(self, mailbox: BaseMailBox, message: MailMessage):
        mailbox.delete([message.uid])

    def format(self, message):
        return f"DELETE {format_message(message)}"


class FlagAction(BaseAction):
    action: Literal["flag"] = "flag"
    flag: Flag

    def _apply(self, mailbox: BaseMailBox, message: MailMessage):
        mailbox.flag([message.uid], flag_set={self.flag.imap}, value=True)

    def format(self, message):
        return f"FLAG {format_message(message)} {self.flag.name}"


class UnflagAction(BaseAction):
    action: Literal["flag"] = "flag"
    flag: Flag

    def _apply(self, mailbox: BaseMailBox, message: MailMessage):
        mailbox.flag([message.uid], flag_set={self.flag.imap}, value=False)

    def format(self, message):
        return f"UNFLAG {format_message(message)} {self.flag.name}"


Action = Union[MoveAction, DeleteAction, FlagAction, UnflagAction]


class ActionLoader(BaseModel):
    __root__: Action
