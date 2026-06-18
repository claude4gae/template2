// 파일 경로: src/features/timeline/components/logDetail/CtttmDetail.jsx
import React from "react";
import Field from "./Field";

export default function CtttmDetail({ log }) {
  return (
    <>
      <Field label="Log Type" value={log.logType} />
      <Field label="CTTTM" value={log.eventType} />
      <Field label="Time" value={log.eventTime} />
      <Field label="Operator" value={log.operator} />
      <Field
        label="Comment"
        value={log.comment}
        className="col-span-2"
        streaming={true}
      />
      <Field
        label="Summary"
        value={log.summary}
        className="col-span-2"
        streaming={true}
      />
    </>
  );
}
