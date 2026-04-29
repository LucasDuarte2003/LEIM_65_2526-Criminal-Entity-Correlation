import { useState, useEffect } from "react";
import { getLabels } from "../api/client.jsx";

export function useLabels() {
  const [labels, setLabels] = useState([]);
  const [labelMap, setLabelMap] = useState({});

  useEffect(() => {
    getLabels()
      .then((data) => {
        setLabels(data);
        const map = {};
        data.forEach((l) => { map[l.nome] = l.cor; });
        setLabelMap(map);
      })
      .catch(console.error);
  }, []);

  return { labels, labelMap };
}