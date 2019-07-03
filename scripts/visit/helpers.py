""" Type helping """

from syntax.ast import add_private_type
from utils.typehelpers import real_types

def linearize_type(t):
    return t.replace(' ', '_').replace('[', '_').replace(']', '')

def network_convert(ast, typ, to_network, name):
    """
    convert type to network order
    basically checks if the type is like int (ie, int, long, or typedef to it)
    this needs to be formatted (with val)
    """
    real_typ = next((t['old'] for t in ast['typedefs'] if t['new'] == typ), typ);
    if '*' in name:
        lval = name;
    else:
        lval = 'int tmp'

    if 'int' in real_typ or 'long' in real_typ or 'short' in real_typ:
        if '64' in real_typ or 'long long' in real_typ:
            if to_network:
                code = \
'''  uint64_t __tmp = {n};
  if (htonl(1) != 1) {{
    uint64_t __high = htonl({n} & ((((uint64_t)1) << 32) - 1));
    uint64_t __low  = htonl({n} >> 32);
    __tmp = (__high << 32) + __low;
  }}
  {l} = __tmp;'''
                return code.format(n = name, l = lval).replace('{', '{{').replace('}', '}}')
            else:
                code =  \
'''  uint64_t __tmp = {n};
  if (ntohl(1) != 1) {{
    uint64_t __high = ntohl({n} & ((((uint64_t)1) << 32) - 1));
    uint64_t __low  = ntohl({n} >> 32);
    __tmp = (__high << 32) + __low;
  }}
  {l} = __tmp;'''

                return code.format(n = name, l = lval).replace('{', '{{').replace('}', '}}')
        elif '32' in real_typ or real_typ == 'int':
            if to_network:
                return '  {l} = htonl({n});\n'.format(n = name, l = lval)
            else:
                return '  {l} = ntohl({n});\n'.format(n = name, l = lval)
        elif '16' in real_typ or 'short' in real_typ:
            if to_network:
                return '  {l} = htons({n});\n'.format(n = name, l = lval)
            else:
                return '  {l} = ntohs({n});\n'.format(n = name, l = lval)
    return None;

def struct_size(s):
    return ' + '.join(['sizeof({t})'.format(t = m[0]) for m in s['members']])

def fun_size(ast, f):
    def real_t(t, real): return real[t] if t in real else t;
    sizes = ['sizeof(uint8_t)', 'sizeof(int32_t)']
    real = real_types(ast)
    for arg in f['args']:
        if arg[0] in ast['private_types'].union(ast['exported_types']):
            sizes.append('sizeof('+real_t(arg[0], real)+')')
        elif any(arg[0] == s['typedef'] for s in ast['structs']):
            sizes.append(struct_size(next(s for s in ast['structs'] if arg[0] == s['typedef'])))
        else:
            add_private_type(ast, arg[0])
            sizes.append('sizeof('+real_t(arg[0], real)+')')

    return ' + '.join(sizes);

def fun_ret_size(ast, f):
    sizes = ['sizeof(uint8_t)', 'sizeof(int32_t)']
    if f['return_t'] in ast['private_types'].union(ast['exported_types']):
        sizes.append('sizeof('+f['return_t']+')')
    elif any(f['return_t'] == s['typedef'] for s in ast['structs']):
        sizes.append(struct_size(next(s for s in ast['structs'] if f['return_t'] == s['typedef'])))
    else:
        add_private_type(ast, f['return_t'])
        sizes.append('sizeof('+f['return_t']+')')

    return ' + '.join(sizes);

def gen_type_decl(t_list):
    def find_slice(s):
        first = s.find('[')
        if first == -1: return None
        last = [p for p, c in enumerate(s) if c == ']'][-1]
        return (first, last + 1)

    s = ' '.join(t_list)
    slic = find_slice(s)
    if slic:
        first = slic[0]
        last = slic[1]
        s = s[:first] + s[last:] + s[first:last]
    return s;

def arg_list(f, full):
    if full:
        return ', '.join(gen_type_decl(arg) for arg in f['args'])
    else:
        return ', '.join(arg[0] for arg in f['args'])
