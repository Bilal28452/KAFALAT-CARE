def badge(label, kind='success'):
    return f'<span class="badge rounded-pill badge-soft-{kind}">{label}</span>'


def initials(name):
    return ''.join(part[0] for part in name.split()[:2]).upper() or 'NA'


def format_money(amount, currency='PKR'):
    if amount is None:
        return f'{currency} 0'
    return f'{currency} {amount:,.0f}'
