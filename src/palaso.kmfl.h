/* Generated by Cython 0.29.27 */

#ifndef __PYX_HAVE__palaso__kmfl
#define __PYX_HAVE__palaso__kmfl

#include "Python.h"

/* "lib/palaso.kmfl.pyx":7
 * from os import PathLike
 * 
 * ctypedef public unsigned int UINT             # <<<<<<<<<<<<<<
 * 
 * cdef extern from "kmfl/kmfl.h" :
 */
typedef unsigned int UINT;

#ifndef __PYX_HAVE_API__palaso__kmfl

#ifndef __PYX_EXTERN_C
  #ifdef __cplusplus
    #define __PYX_EXTERN_C extern "C"
  #else
    #define __PYX_EXTERN_C extern
  #endif
#endif

#ifndef DL_IMPORT
  #define DL_IMPORT(_T) _T
#endif

__PYX_EXTERN_C void output_string(PyObject *, char *);
__PYX_EXTERN_C void output_beep(PyObject *);
__PYX_EXTERN_C void forward_keyevent(PyObject *, UINT, UINT);
__PYX_EXTERN_C void erase_char(PyObject *);

#endif /* !__PYX_HAVE_API__palaso__kmfl */

/* WARNING: the interface of the module init function changed in CPython 3.5. */
/* It now returns a PyModuleDef instance instead of a PyModule instance. */

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC initkmfl(void);
#else
PyMODINIT_FUNC PyInit_kmfl(void);
#endif

#endif /* !__PYX_HAVE__palaso__kmfl */
