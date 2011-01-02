#include <stdio.h>
#include <math.h>
#include <string.h>
#include <Python.h>

static PyObject *
find_closest(PyObject *self, PyObject *args) {
/*int find_closest(char *palette_fn, int or, int og, int ob) {*/
    char *palette_fn;
    int or, og, ob;
    int r, g, b, closest, delta, closest_delta;
    int i, j;
    char line[200], name[40], closest_name[40], ret[10], suffix;
    FILE *palette;

    if (!PyArg_ParseTuple(args, "siii", &palette_fn, &or, &og, &ob)){
        return NULL;
    }

    palette = fopen(palette_fn, "r");
    if (palette == NULL) {
        return -1;
    }

    closest_delta = 0x1000000;
    suffix = '~';
    j = 0;

    for(i = 0; fgets(line, sizeof(line), palette) != NULL; i++) {
        sscanf(line, "%d %d %d %s", &r, &g, &b, name);
        delta = pow(r - or, 2) + pow(g - og, 2) + pow(b - ob, 2);
        if (delta < closest_delta) {
            j = i;
            closest_delta = delta;
            strcpy(closest_name, name);
            if (delta == 0) {
                break;
            }
        }
    }

    if (delta == 0) {
        suffix = ' ';
    }
    snprintf(ret, sizeof(ret), "%d%c", j, suffix);
    /*printf("%s", ret);*/
    /*printf("%s\n", closest_name);*/
    fclose(palette);

    return Py_BuildValue("s", ret);
}

PyMethodDef methods[] = {
    {"find_closest", find_closest, METH_VARARGS, "Find closest rgb in a palette"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initfind_closest()
{
    (void) Py_InitModule("find_closest", methods);
}
