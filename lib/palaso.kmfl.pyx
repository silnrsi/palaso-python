import itertools, functools, re
from palaso.kmn.vector import VectorIterator

ctypedef unsigned int UINT

cdef extern from "kmfl/kmfl.h" :
    struct _xstore :
        UINT len
        UINT items

    struct _xrule :
        UINT ilen
        UINT olen
        UINT lhs
        UINT rhs

    struct _xgroup :
        UINT flags
        UINT nrules
        UINT rule1

    struct _xkeyboard :
        UINT group1
        UINT nstores
        UINT ngroups

    ctypedef _xstore XSTORE
    ctypedef _xrule XRULE
    ctypedef _xgroup XGROUP
    ctypedef _xkeyboard XKEYBOARD

    struct _kmsi :
        XKEYBOARD *keyboard
        XGROUP *groups
        XRULE *rules
        XSTORE *stores
        UINT *strings
        UINT *history
        UINT nhistory

cdef enum :
    lshift = 1
    caps = 2
    lctrl = 4
    lalt = 8
    rshift = 16
    ncaps = 32
    rctrl = 64
    ralt = 128
    shift = 9
    ctrl = 68
    alt = 136

cdef enum :
    item_char = 0
    item_keysym
    item_any
    item_index
    item_outs
    item_deadkey
    item_context
    item_nul
    item_return
    item_beep
    item_use
    item_match
    item_nomatch
    item_plus
    item_call
    item_notany

cdef enum :
    ss_undefined = -1
    ss_name
    ss_version
    ss_hotkey
    ss_language
    ss_layout
    ss_copyright
    ss_message
    ss_bitmap
    ss_mnemonic
    ss_ethnologue
    ss_capsoff
    ss_capson
    ss_capsfree
    ss_author

ctypedef _kmsi KMSI

cdef extern from "kmfl/libkmfl.h" :
    KMSI *kmfl_make_keyboard_instance(connection)
    int kmfl_delete_keyboard_instance(KMSI *p_kmsi)
    int kmfl_load_keyboard(char *file)
    int kmfl_unload_keyboard(int keyboard_number)
    int kmfl_attach_keyboard(KMSI *p_kmsi, int keyboard_number)
    int kmfl_detach_keyboard(KMSI *p_kmsi)
    int kmfl_interpret(KMSI *p_kmsi, UINT key, UINT state)
    void clear_history(KMSI *p_kmsi)
    void add_to_history(KMSI *p_kmsi, UINT item)

cdef public void output_string(connection, char *p) :
    pass

cdef public void output_beep(connection) :
    connection.beep = 1

cdef public void forward_keyevent(connection, UINT key, UINT state) :
    pass

cdef public void erase_char(connection) :
    pass

cdef item_index_offset(UINT x) : return (x >> 16) & 0xFF
cdef item_base(UINT x) : return x & 0xFFFF
cdef item_type(UINT x) : return (x >> 24) & 0xFF

_storemap = {
    'UNDEFINED' : ss_undefined,
    'NAME'      : ss_name,
    'VERSION'   : ss_version,
    'HOTKEY'    : ss_hotkey,
    'LANGUAGE'  : ss_language,
    'LAYOUT'    : ss_layout,
    'COPYRIGHT' : ss_copyright,
    'MESSAGE'   : ss_message,
    'BITMAP'    : ss_bitmap,
    'MNEMONIC'  : ss_mnemonic,
    'ETHNOLOGUE' : ss_ethnologue,
    'CAPSOFF'   : ss_capsoff,
    'CAPSON'    : ss_capson,
    'CAPSFREE'  : ss_capsfree,
    'AUTHOR'    : ss_author
}

cdef class kmfl :

    cdef KMSI *kmsi
    cdef int kbd

    def __init__(self, fname) :
        self.kmsi = kmfl_make_keyboard_instance(self)
        self.kbd = kmfl_load_keyboard(fname)
        if self.kbd >= 0 :
            kmfl_attach_keyboard(self.kmsi, self.kbd)
        else :
            raise SyntaxError("Can't load keyboard " + fname)
        self.numrules = self._num_rules()

    def __del__(self) :
        kmfl_detach_keyboard(self.kmsi)
        kmfl_unload_keyboard(self.kbd)
        kmfl_delete_keyboard_instance(self.kmsi)

    def _num_rules(self) :
        res = 0
        for 0 <= i < self.kmsi.keyboard.ngroups :
            res += self.kmsi.groups[i].nrules
        return res

    def rule(self, num) :
        """ Returns a given rule as a tuple:
            (left context, right output, group number, flags)
        """
        cdef XRULE rule
        cdef UINT *base
        count = 0
        flags = 0
        for 0 <= gpnum < self.kmsi.keyboard.ngroups :
            count += self.kmsi.groups[gpnum].nrules
            if count >= num :
                flags = self.kmsi.groups[gpnum].flags
                break
        rule = self.kmsi.rules[num]
        base = self.kmsi.strings + rule.lhs
        lhs = []
        for 0 <= i < rule.ilen :
            lhs.append(base[i])
        base = self.kmsi.strings + rule.rhs
        rhs = []
        for 0 <= i < rule.olen :
            rhs.append(base[i])
        return (lhs, rhs, gpnum, flags)

    def run_items(self, items) :
        """ Executes a sequence of items returning the output character string """
        clear_history(self.kmsi)
        for i in items :
            mod = (i >> 16) & 0xFF
            mod = ((mod & 0xF0) << 4) | (mod & 0x0F)
            kmfl_interpret(self.kmsi, i & 0xFFFF, mod)
        res = []
        for 1 <= i <= self.kmsi.nhistory :
            if item_type(self.kmsi.history[i]) == 0 :
                res.insert(0,unichr(self.kmsi.history[i]))
        return "".join(res)

    def interpret_items(self, items) :
        """ Executes a sequence of items returning the item history at the end of the sequence """
        clear_history(self.kmsi)
        for i in items :
            if item_type(i) > 1 :
                add_to_history(self.kmsi, i)
            else :
                kmfl_interpret(self.kmsi, i & 0xFFFF, ((i >> 16) & 0x0F) | ((i >> 12) & 0x0F00))
        res = []
        for 1 <= i <= self.kmsi.nhistory :
            res.insert(0,self.kmsi.history[i])
        return res

    def reverse_match(self, input, rulenum, mode = 'all') :
        """Given a rule and an input context, matches the end of the input context
            against the output of the rule, if it matches, returns all possible
            lhs contexts that will produce this output

            input : list of numeric items as the input context
            rulenum : number of rule to search against
            returns : (len, contexts)
                len : amount of input to consume from the right
                contexts : list of lists of items, each list is one context"""
        cdef UINT ruleitem, lcount, i, j, ruletype
        cdef UINT *compares
        cdef XRULE rule
        cdef XSTORE store
        rule = self.kmsi.rules[rulenum]
        linput = len(input) - 1
        indices = [None] * rule.ilen
        for 1 <= i <= rule.olen :
            if linput < 0 : return None
            ruleitem = self.kmsi.strings[rule.rhs + rule.olen - i]
            ruletype = item_type(ruleitem)
            if ruletype == item_outs :
                store = self.kmsi.stores[item_base(ruleitem)]
                compares = self.kmsi.strings + store.items
                comparel = store.len
                for 0 <= j < comparel :
                    if compares[j] != item_base(input[linput-j]) : return None
                linput = linput - comparel
            else :
                if ruletype == item_context :
                    lcount = rule.ilen - 1
                    lbase = rule.lhs + lcount - 1
                else :
                    lcount = 1
                    lbase = rule.rhs + rule.olen - i
                if lcount > len(input) - i + 1 : return None
                for 0 <= j < lcount :
                    index = self.test_match(input[linput-j], self.kmsi.strings[lbase-j])
                    if index == None : return None
                    if index[0] != None :
                        if indices[index[0]] != None and indices[index[0]] != index[1] : return None
                        indices[index[0]] = index[1]
                linput = linput - lcount
        expand_rule_context = functools.partial(self.expand_context, rulenum, side= 'l')
        return (len(input) - linput - 1, itertools.imap(expand_rule_context,VectorIterator(indices, mode)))

    def test_match(self, UINT charitem, UINT ritem) :
        """ Compares two items to see if the first is matched by the second in a rule context """
        simpleres = (None, ())
        ruleitem = item_type(ritem)
        if ruleitem == item_char or ruleitem == item_deadkey or ruleitem == item_keysym :
            if charitem == ritem : return simpleres
            return None
        elif ruleitem == item_index or ruleitem == item_any :
            res = self.match_store(item_base(ritem), item_base(charitem))
            if res == None : return None
            return (item_index_offset(ritem) - 1, tuple(res))
        else :
            return None

    def expand_context(self, UINT rulenum, vector, side = 'r') :
        """ returns an expansion of a context string (either left or right - output)
            based on the vector which specifies which element to take in a store, for example """
        cdef XSTORE s
        cdef UINT *items, *context, clen, ci
        if side == 'r' :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].rhs
            clen = self.kmsi.rules[rulenum].olen
        else :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].lhs
            clen = self.kmsi.rules[rulenum].ilen
        res = []
        for 0 <= i < clen :
            ci = context[i]           
            ruleitem = item_type(ci)
            if ruleitem == item_char or ruleitem == item_deadkey or ruleitem == item_keysym :
                res.append(ci)
            elif ruleitem == item_index or ruleitem == item_any :
                items = self.kmsi.strings + self.kmsi.stores[item_base(ci)].items
                if ruleitem == item_index :
                    res.append(items[vector[item_index_offset(ci) - 1]])
                else :
                    res.append(items[vector[i]])
            elif ruleitem == item_outs :
                s = self.kmsi.stores[item_base(ci)]
                items = self.kmsi.strings + s.items
                for 0 <= j < s.len :
                    res.append(items[j])
            elif ruleitem == item_context :
                if side == 'r' :
                    res.extend(self.expand_context(rulenum, vector, side = 'l'))
                else :
                    res.extend(self.expand_context(rulenum, vector, side = 'r'))
        return res

    def flatten_context(self, UINT rulenum, side = 'l', mode = 'all') :
        """ Returns all/some the possible item strings for a given context in a rule
                mode = all      - all strings
                       first1   - just the first string
                       random   - one string per element in the context
                       random-all - all strings in a random order, top down
                       random-all-depth - all strings in a random order, bottom up
                       random1  - just one random string
        """
        cdef UINT *context, clen, ci
        if side == 'r' :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].rhs
            clen = self.kmsi.rules[rulenum].olen
        else :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].lhs
            clen = self.kmsi.rules[rulenum].ilen
        indices = [None] * clen
        for 0 <= i < clen :
            ci = context[i]
            ruleitem = item_type(ci)
            if ruleitem == item_any :
                indices[i] = range(0, self.kmsi.stores[item_base(ci)].len)
            elif ruleitem == item_index :
                indices[item_index_offset(ci) - 1] = range(0, self.kmsi.stores[item_base(ci)].len)
        expand_rule_context = functools.partial(self.expand_context,rulenum,side=side)
        return itertools.imap(expand_rule_context, VectorIterator(indices, mode = mode))

    def match_store(self, UINT snum, UINT item) :
        """ Returns whether an item is matched in a store, and if so, its index, else None """
        cdef UINT i
        cdef XSTORE s
        cdef UINT *items
        s = self.kmsi.stores[snum]
        items = self.kmsi.strings + s.items
        res = []
        for 0 <= i < s.len :
            if items[i] == item : res.append(i)
        if len(res) == 0 :
            return None
        return res

    def store(self, sname) :
        """ returns a given store by name or number. No bounds checking
            is done (because none is possible!)"""
        cdef UINT i
        cdef UINT snum
        cdef XSTORE s
        cdef UINT *items
        res = ""
        snum = _storemap.get(sname.upper(), -1)
        if snum == -1 :
            snum = int(sname)

        if snum >= self.kmsi.keyboard.nstores : 
            print "%d >= %d" % (snum, self.kmsi.keyboard.nstores)
            return res
        s = self.kmsi.stores[snum]
        items = self.kmsi.strings + s.items
        for 0 <= i < s.len :
            res = res + unichr(items[i])
        return res

