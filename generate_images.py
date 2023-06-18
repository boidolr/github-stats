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


def generate_output_folder() -> None:
    """
    Create the output folder if it does not already exist
    """
    pathlib.Path("generated").mkdir(exist_ok=True)


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
    with open("templates/overview.svg", "r") as f:
        template = f.read()

    replacements = {
        "name": await s.name,
        "stars": f"{(await s.stargazers):,}",
        "forks": f"{(await s.forks):,}",
        "contributions": f"{(await s.total_contributions):,}",
        "lines_changed": f"{sum(await s.lines_changed)}",
        "views": f"{await s.views:,}",
        "repos": f"{len(await s.repos):,}",
    }

    light = create_svg(template, replacements, "light")
    dark = create_svg(template, replacements, "dark")

    generate_output_folder()
    with open("generated/overview.svg", "w") as f:
        f.write(light)
    with open("generated/overview-dark.svg", "w") as f:
        f.write(dark)
    with open("generated/overview-light.svg", "w") as f:
        f.write(light)


async def generate_languages(s: Stats) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    with open("templates/languages.svg", "r") as f:
        template = f.read()

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
            """
        )

    replacements = {
        "progress": "".join(progress),
        "lang_list": "".join(lang_list[:4]),
    }
    light = create_svg(template, replacements, "light")
    dark = create_svg(template, replacements, "dark")

    generate_output_folder()
    with open("generated/languages.svg", "w") as f:
        f.write(light)
    with open("generated/languages-dark.svg", "w") as f:
        f.write(dark)
    with open("generated/languages-light.svg", "w") as f:
        f.write(light)


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
