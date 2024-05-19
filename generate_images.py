#!/usr/bin/python3

import asyncio
import os
import pathlib
import re

import aiohttp

from github_stats import Stats


################################################################################
# Helper Functions
################################################################################


def create_svg(template: str, replacements: dict[str, str], theme: str) -> str:
    colors = (
        {
            "var_color": "#57a6ff",
            "var_heading": "#8b949e",
            "var_accent": "#484f58",
        }
        if theme == "dark"
        else {
            "var_color": "#24292f",
            "var_heading": "#0969da",
            "var_accent": "#6e7781",
        }
    )
    variables = {
        **colors,
        **replacements,
    }

    def replacer(match: re.Match) -> str:
        return variables.get(match.group(1), "")

    return re.sub("{{ ([a-z_]+) }}", replacer, template)


################################################################################
# Individual Image Generation Functions
################################################################################


async def generate_overview(s: Stats) -> None:
    """
    Generate an SVG badge with summary statistics
    :param s: Represents user's GitHub statistics
    """

    replacements = {
        "name": await s.name,
        "stars": f"{(await s.stargazers):,}",
        "forks": f"{(await s.forks):,}",
        "contributions": f"{(await s.total_contributions):,}",
        "lines_changed": f"{sum(await s.lines_changed)}",
        "views": f"{await s.views:,}",
        "repos": f"{len(await s.repos):,}",
    }

    template = pathlib.Path("templates/overview.svg").read_text()
    light = create_svg(template, replacements, "light")
    dark = create_svg(template, replacements, "dark")

    pathlib.Path("generated").mkdir(exist_ok=True)
    pathlib.Path("generated/overview.svg").write_text(light)
    pathlib.Path("generated/overview-dark.svg").write_text(dark)
    pathlib.Path("generated/overview-light.svg").write_text(light)


async def generate_languages(s: Stats) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    progress = []
    lang_list = []
    sorted_languages = sorted(
        (await s.languages).items(), reverse=True, key=lambda t: t[1].get("size")
    )[:10]
    delay_between = 50
    for i, (lang, data) in enumerate(sorted_languages):
        color = data.get("color")
        prop = data.get("prop", 0)
        color = color if color is not None else "#000000"
        progress.append(
            f'<span style="background-color: {color};'
            f'width: {prop:0.3f}%;" '
            f'class="progress-item"></span>'
        )
        lang_list.append(f"""\
            <li style="animation-delay: {i * delay_between}ms;">
            <svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{color};"
            viewBox="0 0 16 16" version="1.1" width="16" height="16"><path
            fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
            <span class="lang">{lang}</span>
            <span class="percent">{prop:0.2f}%</span>
            </li>
            """)

    replacements = {
        "progress": "".join(progress),
        "lang_list": "".join(lang_list[:4]),
    }

    template = pathlib.Path("templates/languages.svg").read_text()
    light = create_svg(template, replacements, "light")
    dark = create_svg(template, replacements, "dark")

    pathlib.Path("generated").mkdir(exist_ok=True)
    pathlib.Path("generated/languages.svg").write_text(light)
    pathlib.Path("generated/languages-dark.svg").write_text(dark)
    pathlib.Path("generated/languages-light.svg").write_text(light)


################################################################################
# Main Function
################################################################################


async def main() -> None:
    """
    Generate all badges
    """
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        # access_token = os.getenv("GITHUB_TOKEN")
        raise Exception("A personal access token is required to proceed!")
    user = os.getenv("GITHUB_ACTOR")
    exclude_repos = os.getenv("EXCLUDED")
    exclude_repos = (
        {x.strip() for x in exclude_repos.split(",")} if exclude_repos else None
    )
    exclude_langs = os.getenv("EXCLUDED_LANGS")
    exclude_langs = (
        {x.strip() for x in exclude_langs.split(",")} if exclude_langs else None
    )
    # Convert a truthy value to a Boolean
    ignore_forked_repos = os.getenv("EXCLUDE_FORKED_REPOS")
    ignore_forked_repos = (
        not not ignore_forked_repos and ignore_forked_repos.strip().lower() != "false"
    )
    async with aiohttp.ClientSession() as session:
        s = Stats(
            user,
            access_token,
            session,
            exclude_repos=exclude_repos,
            exclude_langs=exclude_langs,
            ignore_forked_repos=ignore_forked_repos,
        )
        await asyncio.gather(generate_languages(s), generate_overview(s))


if __name__ == "__main__":
    asyncio.run(main())
