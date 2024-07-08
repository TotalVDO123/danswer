"use client";

import { aiOptionsData } from "./data/aiOptions";
import { useState } from "react";

export default function AIOptions() {
  const categories = Array.from(
    new Set(aiOptionsData.map((data) => data.category))
  );

  const [activeCategory, setActiveCategory] = useState(categories[0]);

  const handleCategoryClick = (category: string) => {
    setActiveCategory(category);
  };

  return (
    <div className="flex flex-col items-center gap-12 pt-10">
      <div className="flex gap-4">
        {categories.map((category) => (
          <button
            key={category}
            className={`text-lg px-3 py-2 rounded-[5px] ease-out duration-500 transition-all ${
              category === activeCategory
                ? "bg-[#D7EAFF] text-[#64A3FF] hover:opacity-50"
                : "hover:bg-[rgba(14,_14,_15,_0.1)]"
            }`}
            onClick={() => handleCategoryClick(category)}
          >
            {category}
          </button>
        ))}
      </div>

      <div className="flex justify-between w-full gap-8">
        {aiOptionsData
          .filter((data) => data.category === activeCategory)
          .map((data, i) => (
            <div key={i} className="flex flex-col items-start w-1/3 gap-6">
              <h3 className="text-xl font-semibold text-black">{data.title}</h3>
              <p>{data.description}</p>
              <button className="text-[#2039F3] font-bold">Learn more</button>
            </div>
          ))}
      </div>

      <div className="flex items-center text-lg font-semibold gap-14">
        <button className="py-3 px-6 bg-[#2039F3] text-white rounded-[5px]">
          Get a Demo
        </button>
        <button className="text-[#2039F3]">Start for free</button>
      </div>
    </div>
  );
}
