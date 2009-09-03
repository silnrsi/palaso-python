import re
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

cdef class kmfl :

    cdef KMSI *kmsi
    cdef UINT kbd

    def __init__(self, fname) :
        self.kmsi = kmfl_make_keyboard_instance(self)
        self.kbd = kmfl_load_keyboard(fname)
        if self.kbd >= 0 :
            kmfl_attach_keyboard(self.kmsi, self.kbd)
        else :
            raise SyntaxError("Can't load keyboard " + fname)

    def __del__(self) :
        kmfl_detach_keyboard(self.kmsi)
        kmfl_unload_keyboard(self.kbd)
        kmfl_delete_keyboard_instance(self.kmsi)

    def num_rules(self) :
        return self.kmsi.groups[self.kmsi.keyboard.group1].nrules

    def rule(self, num) :
        cdef XRULE rule
        cdef UINT *base
        rule = self.kmsi.rules[num]
        base = self.kmsi.strings + rule.lhs
        lhs = []
        for 0 <= i < rule.ilen :
            lhs.append(base[i])
        base = self.kmsi.strings + rule.rhs
        rhs = []
        for 0 <= i < rule.olen :
            rhs.append(base[i])
        return (lhs, rhs)

    def run_items(self, items) :
        clear_history(self.kmsi)
        for i in items :
            kmfl_interpret(self.kmsi, i & 0xFFFF, (i >> 16) & 0xFF)
        res = []
        for 1 <= i <= self.kmsi.nhistory :
            res.append(self.kmsi.history[i])
        res.reverse()
        return "".join(map(unichr, res))

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
        rule = self.kmsi.rules[rulenum]
        linput = len(input)
        if rule.olen > linput : return None
        indices = [None] * rule.ilen
        for 1 <= i <= rule.olen :
            ruleitem = self.kmsi.strings[rule.rhs + rule.olen - i]
            ruletype = item_type(ruleitem)
            if ruletype == item_outs :
                compares = self.kmsi.strings + self.kmsi.stores[item_base(ruleitem)].items
                comparel = self.kmsi.stores[item_base(ruleitem)].len
                for 0 <= j < comparel :
                    if compares[j] != item_base(input[linput-i-j]) : return None
                i = i + comparel - 1
            else :
                if ruletype == item_context :
                    lcount = rule.ilen - 1
                    lbase = rule.lhs + rule.ilen
                else :
                    lcount = 1
                    lbase = rule.rhs + rule.olen
                if lcount > len(input) - i + 1 : return None
                for 0 <= j < lcount :
                    index = self.test_match(input[linput-i-j], self.kmsi.strings[lbase - j - i])
                    if index == None : return None
                    if index[0] != None :
                        if indices[index[0]] != None and indices[index[0]] != index[1] : return None
                        indices[index[0]] = index[1]
                i = i + lcount - 1
        vector = VectorIterator(indices, mode)
        result = []
        while vector != None :
            result.append(self.expand_context(rulenum, vector.vector, side = 'l'))
            vector = vector.advance()
        return (rule.olen, result)

    def test_match(self, UINT charitem, UINT ritem) :
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
        cdef XSTORE s
        cdef UINT *items, *context, clen
        if side == 'r' :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].rhs
            clen = self.kmsi.rules[rulenum].olen
        else :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].lhs
            clen = self.kmsi.rules[rulenum].ilen
        res = []
        for 0 <= i < clen :
            ruleitem = item_type(context[i])
            if ruleitem == item_char or ruleitem == item_deadkey or ruleitem == item_keysym :
                res.append(context[i])
            elif ruleitem == item_index or ruleitem == item_any :
                items = self.kmsi.strings + self.kmsi.stores[item_base(context[i])].items
                if ruleitem == item_index :
                    res.append(items[vector[item_index_offset(context[i]) - 1]])
                else :
                    res.append(items[vector[i]])
            elif ruleitem == item_outs :
                s = self.kmsi.stores[item_base(context[i])]
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
        cdef UINT *context, clen
        if side == 'r' :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].rhs
            clen = self.kmsi.rules[rulenum].olen
        else :
            context = self.kmsi.strings + self.kmsi.rules[rulenum].lhs
            clen = self.kmsi.rules[rulenum].ilen
        indices = [None] * clen
        for 0 <= i < clen :
            ruleitem = item_type(context[i])
            if ruleitem == item_any :
                indices[i] = range(0, self.kmsi.stores[item_base(context[i])].len)
            elif ruleitem == item_index :
                indices[item_index_offset(context[i]) - 1] = range(0, self.kmsi.stores[item_base(context[i])].len)
        result = []
        vector = VectorIterator(indices, mode = mode)
        while vector != None :
            result.append(self.expand_context(rulenum, vector.vector, side = side))
            vector = vector.advance()
        return result

    def match_store(self, UINT snum, UINT item) :
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

