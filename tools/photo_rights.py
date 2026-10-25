"""Image rights statements from the reviewed source credits, without new ownership claims."""
import re


def image_rights(photo):
    author = photo['author'].strip()
    name = re.sub(r'^©\s*', '', (photo.get('attribution') or author).strip())
    if not name or len(name) > 150:
        raise ValueError('A concise, source-backed creator name is required')
    # Official press credits and the recorded publishing channels identify organizations.
    organization = photo.get('usage') == 'editorial-only' or photo.get('credit', '').startswith('YouTube :')
    creator = {'@type': 'Organization' if organization else 'Person', 'name': name}
    if '/publicdomain/zero/' in photo['license_url']:
        notice = 'CC0 1.0 Universal (public domain-dedikation). Foto: ' + name + '.'
    elif author.startswith('©'):
        notice = author
    else:
        # Preserve the source attribution and license; invent neither an owner nor a year.
        notice = name + ' / ' + photo['license']
    return {'creator': creator, 'copyrightNotice': notice}
