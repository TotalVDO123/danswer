import { FiCheck, FiChevronDown } from "react-icons/fi";
import { CustomDropdown } from "../../Dropdown";

interface Option {
  key: string;
  display: string | JSX.Element;
}

export function FilterDropdown({
  options,
  selected,
  handleSelect,
  icon,
  defaultDisplay,
}: {
  options: Option[];
  selected: string[];
  handleSelect: (option: Option) => void;
  icon: JSX.Element;
  defaultDisplay: string | JSX.Element;
}) {
  return (
    <div className="w-64">
      <CustomDropdown
        dropdown={
          <div
            className={`
          border 
          border-gray-800 
          rounded-lg 
          flex 
          flex-col 
          w-64 
          max-h-96 
          overflow-y-auto 
          overscroll-contain`}
          >
            {options.map((option, ind) => {
              const isSelected = selected.includes(option.key);
              return (
                <div
                  key={option.key}
                  className={`
                    flex
                    px-3 
                    text-sm 
                    text-gray-200 
                    py-2.5 
                    select-none 
                    cursor-pointer 
                    ${
                      ind === options.length - 1
                        ? ""
                        : "border-b border-gray-800"
                    } 
                    ${
                      isSelected
                        ? "bg-dark-tremor-background-muted"
                        : "hover:bg-dark-tremor-background-muted "
                    }
                  `}
                  onClick={(event) => {
                    handleSelect(option);
                    event.preventDefault();
                    event.stopPropagation();
                  }}
                >
                  {option.display}
                  {isSelected && (
                    <div className="ml-auto mr-1">
                      <FiCheck />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        }
      >
        <div
          className={`
        flex 
        w-64
        text-sm 
        text-gray-400 
        px-3
        py-1.5 
        rounded-lg 
        border 
        border-gray-800 
        cursor-pointer 
        hover:bg-dark-tremor-background-muted`}
        >
          {icon}
          {selected.length === 0 ? (
            defaultDisplay
          ) : (
            <p className="text-gray-200 line-clamp-1">{selected.join(", ")}</p>
          )}
          <FiChevronDown className="my-auto ml-auto" />
        </div>
      </CustomDropdown>
    </div>
  );
}
