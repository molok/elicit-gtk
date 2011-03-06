#include <stdio.h>
#include <math.h>
#include <string.h>
#include <Python.h>

int initialized = 0;
char *palette;

static PyObject *
find_closest_init(PyObject *self, PyObject *args) {
    extern char *palette;
    char *p;

    if (!PyArg_ParseTuple(args, "s", &p)) {
        return Py_BuildValue("i", -1);
    }

    palette = strdup(p);

    return Py_BuildValue("i", 0);
}

static PyObject *
find_closest(PyObject *self, PyObject *args) {
/*int find_closest(char *palette_fn, int or, int og, int ob) {*/
    int or, og, ob;
    int r, g, b, delta, closest_delta;
    int i, j;
    char line[200], ret[10], suffix, name[40];
    FILE *palette_stream;
    extern int initialized;
    extern char *palette;


    if (!PyArg_ParseTuple(args, "iii", &or, &og, &ob)) {
        return Py_BuildValue("i", -1);
    }

    palette_stream = fmemopen(palette, strlen (palette), "r");

    if (palette_stream == NULL) {
        return Py_BuildValue("i", -2);
    }

    closest_delta = 0x1000000;
    suffix = '~';
    j = 0;
    delta = 0;

    for(i = 0; fgets(line, sizeof(line), palette_stream) != NULL; i++) {
        sscanf(line, "%d, %d, %d", &r, &g, &b);
        /*printf("Just read  r:%d g:%d b:%d\n", r, g, b);*/
        delta = pow(r - or, 2) + pow(g - og, 2) + pow(b - ob, 2);
        if (delta < closest_delta) {
            j = i;
            closest_delta = delta;
            if (delta == 0) {
                break;
            }
        }
    }

    if (delta == 0) {
        suffix = ' ';
    }
    snprintf(ret, sizeof(ret), "%d%c", j, suffix);

    fclose(palette_stream);
    return Py_BuildValue("s", ret);
}

PyMethodDef methods[] = {
    {"find_closest", find_closest, METH_VARARGS, "Find closest rgb in a palette"},
    {"find_closest_init", find_closest_init, METH_VARARGS, "Initialize palette"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initfind_closest()
{
    (void) Py_InitModule("find_closest", methods);
}
