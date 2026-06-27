from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.prompt import Prompt
from rich import box
from modules.tempmailq import TempMailQ

console = Console()

ACTIONS = {
    "1": "Refresh Inbox",
    "2": "New Email",
    "3": "History",
    "4": "Delete & Regenerate",
    "5": "Exit",
}


def header(site):
    email = site.current_email or "..."
    console.print(Panel(
        f"[bold white]{email}[/]  [dim]| tempmailq.com[/]",
        title="[bold cyan]TempMail[/]",
        border_style="cyan",
        padding=(0, 2),
    ))


def menu():
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="bold cyan", width=3)
    t.add_column(style="white")
    for k, v in ACTIONS.items():
        t.add_row(k, v)
    console.print(t)


def show_inbox(messages):
    if not messages:
        console.print("[dim]  Inbox is empty.[/]")
        return
    t = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1), expand=True)
    t.add_column("#",      style="dim",        width=3, justify="right")
    t.add_column("From",   style="cyan",        ratio=2)
    t.add_column("Subject",style="white bold",  ratio=3)
    t.add_column("Time",   style="dim",         ratio=2)
    for i, m in enumerate(messages, 1):
        t.add_row(str(i), m["sender"], m["subject"], m["time"])
    console.print(t)


def show_message(msg):
    meta = Text()
    meta.append("From:    ", style="dim")
    meta.append(f"{msg['sender']}\n", style="cyan")
    meta.append("Subject: ", style="dim")
    meta.append(f"{msg['subject']}\n", style="bold white")
    meta.append("Time:    ", style="dim")
    meta.append(msg["time"], style="dim")
    console.print(Panel(meta, border_style="dim", padding=(0, 2)))
    console.print(Panel(msg["body"] or "(empty)", border_style="dim cyan", padding=(1, 2)))
    if msg["links"]:
        console.print("[dim]Links:[/]")
        for lnk in msg["links"]:
            console.print(f"  [cyan underline]{lnk}[/]")


def show_history(history, current):
    if not history:
        console.print("[dim]  No history.[/]")
        return
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim",  width=3)
    t.add_column(style="white")
    for i, email in enumerate(history, 1):
        style = "bold cyan" if email == current else "white"
        t.add_row(str(i), f"[{style}]{email}[/]")
    console.print(t)


def main():
    console.clear()
    with console.status("[cyan]Connecting...[/]"):
        site = TempMailQ()

    messages = []

    while True:
        console.rule()
        header(site)
        menu()

        cmd = Prompt.ask("[cyan]>[/]", default="").strip()

        if cmd == "1":
            with console.status("[cyan]Refreshing...[/]"):
                messages = site.refresh_emails()
            show_inbox(messages)
            if messages:
                pick = Prompt.ask("[dim]Open # (enter to skip)[/]", default="").strip()
                if pick.isdigit():
                    idx = int(pick) - 1
                    if 0 <= idx < len(messages):
                        show_message(messages[idx])

        elif cmd == "2":
            alias  = Prompt.ask("[dim]Alias (blank = random)[/]", default="").strip() or None
            domain = Prompt.ask("[dim]Domain[/]", default="wqacmjaqe.xyz").strip()
            with console.status("[cyan]Creating...[/]"):
                result = site.create_email(alias=alias, domain=domain)
            if result:
                console.print(f"[green]Created:[/] {result}")
            else:
                console.print("[red]Failed.[/]")

        elif cmd == "3":
            history = site.list_history()
            show_history(history, site.current_email)
            if history:
                pick = Prompt.ask("[dim]Switch to # (enter to skip)[/]", default="").strip()
                if pick.isdigit():
                    idx = int(pick) - 1
                    if 0 <= idx < len(history):
                        alias, domain = history[idx].split("@", 1)
                        with console.status("[cyan]Switching...[/]"):
                            result = site.create_email(alias=alias, domain=domain)
                        if result:
                            console.print(f"[green]Switched:[/] {result}")
                        else:
                            console.print("[red]Switch failed.[/]")

        elif cmd == "4":
            old = site.current_email
            with console.status("[cyan]Deleting...[/]"):
                result = site.delete_email()
            if result:
                console.print(f"[dim]Deleted {old}[/]  →  [green]{result}[/]")
            else:
                console.print("[red]Failed.[/]")

        elif cmd == "5" or cmd.lower() in ("exit", "q", "quit"):
            console.print("[dim]bye.[/]")
            break


if __name__ == "__main__":
    main()
