import re

ctypedef unsigned int UINT

cdef extern from "kmfl/kmfl.h" :
    struct _kmsi :
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

cdef class kmfl :

    cdef KMSI *kmsi
    cdef UINT kbd

    def __init__(self, fname) :
        self.kmsi = kmfl_make_keyboard_instance(self)
        self.kbd = kmfl_load_keyboard(fname)
        if self.kbd >= 0 :
            kmfl_attach_keyboard(self.kmsi, self.kbd)

    def __del__(self) :
        kmfl_detach_keyboard(self.kmsi)
        kmfl_unload_keyboard(self.kbd)
        kmfl_delete_keyboard_instance(self.kmsi)


    def run_string(self, keystring) :
#        cdef ks mod
        clear_history(self.kmsi)
        keys = re.split(r"([+^%]*.)", keystring)[1::2]
        for k in keys :
            akey = re.split("[+^%]", k)
            base = akey[-1]
            mod = 0
            for m in akey[1::2] :
                if m == '+' :
                    mod = mod + shift
                elif m == '^' :
                    mod = mod + ctrl
                elif m == '%' :
                    mod = mod + alt
            kmfl_interpret(self.kmsi, ord(base), mod)
            res = []
        for 1 <= i <= self.kmsi.nhistory :
            res.append(self.kmsi.history[i])
        res.reverse()
        return "".join(map(unichr, res))
            
