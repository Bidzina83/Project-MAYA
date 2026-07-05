/**
 * @name Project MAYA output/storage call inventory
 * @description Lists print, logging, JSON dump, and file-write calls for review.
 * @kind problem
 * @problem.severity recommendation
 * @id project-maya/output-storage-call-inventory
 */

import python

predicate isPrintCall(Call c) {
  exists(Name n |
    c.getFunc() = n and
    n.getId() = "print"
  )
}

predicate isLoggerCall(Call c) {
  exists(Attribute a |
    c.getFunc() = a and
    (
      a.getName() = "debug" or
      a.getName() = "info" or
      a.getName() = "warning" or
      a.getName() = "error" or
      a.getName() = "exception" or
      a.getName() = "critical"
    )
  )
}

predicate isJsonDumpCall(Call c) {
  exists(Attribute a |
    c.getFunc() = a and
    (a.getName() = "dumps" or a.getName() = "dump")
  )
}

predicate isFileWriteCall(Call c) {
  exists(Attribute a |
    c.getFunc() = a and
    (
      a.getName() = "write_text" or
      a.getName() = "write" or
      a.getName() = "writelines"
    )
  )
}

from Call c
where
  isPrintCall(c) or
  isLoggerCall(c) or
  isJsonDumpCall(c) or
  isFileWriteCall(c)
select c, "Output/storage call seen by CodeQL."