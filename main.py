import sys
from typing import List, Dict, Any


def parse_arguments() -> List[str]:
    args = sys.argv
    report_name = None

    data_files = []
    result = []
    i = 1
    while i < len(args):
        if args[i] == "--report" and i + 1 < len(args):
            report_name = args[i + 1]
            result.append(report_name)
            i += 2
        else:
            data_files.append(args[i])
            i += 1

    result.append(data_files)
    
    return result
    

def read_csv(filename: str) -> List[Dict[str, str]]:
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        return []

    headers = [h.strip() for h in lines[0].strip().split(',')]
    data = []
    
    for line in lines[1:]:
        if not line.strip():
            continue

        values = [v.strip() for v in line.strip().split(',')]
        if len(values) != len(headers):
            print(f"Осторожно, строка содержит неверное количество значений: {line}")
            continue

        row = {headers[i]: values[i] for i in range(len(headers))}
        data.append(row)
    
    return data

class Report:
    def generate(self, data: List[Dict[str, str]]) -> Any:
        raise NotImplementedError
    
    def format_output(self, result: Any) -> str:
        raise NotImplementedError

class PayoutReport(Report):
    def generate(self, data: List[Dict[str, str]]) -> Dict[str, Any]:
        field_names = ['hourly_rate', 'rate', 'salary']
        departments = {}

        for row in data:
            department = row.get('department', 'Неизвестный отдел')
            name = row.get('name', 'Неизвестный сотрудник')

            field_name = next((name for name in field_names if name in row), None)
            if field_name is None:
                continue
                
            try:
                hours = float(row.get('hours_worked', 0))
                rate = float(row.get(field_name, 0))
                payout = rate * hours

                if department not in departments:
                    departments[department] = {
                        'employees': [],
                        'total_hours': 0,
                        'total_payout': 0,
                    }
                departments[department]['employees'].append({
                    'name': name,
                    'hours': hours,
                    'rate': rate,
                    'payout': payout
                })
                departments[department]['total_hours'] += hours
                departments[department]['total_payout'] += payout

            except ValueError as e:
                print(f"Ошибка преобразования данных: {e}")
                continue
        
        return {'departments': departments}

        

    def format_output(self, result: Dict[str, Any]) -> str:
        output = ""
        departments = result['departments']

        output += f"{'name':>25} {'hours':>22} {'rate':>8} {'payout':>10}\n"

        for department_name, department_data in sorted(departments.items()):
            output += f"{department_name}\n"
        
            for emp in department_data['employees']:
                output += "-" * 20
                output += f"{'':<1}{emp['name']:<16} {int(emp['hours']):>8} {int(emp['rate']):>8} {'':>5} ${int(emp['payout']):<9}\n"
        
            output += f"{'':<37} {int(department_data['total_hours']):>8} {'':<14} ${int(department_data['total_payout']):<8}\n"
        return output

class ReportsData:
    _reports: Dict[str, Any] = {}

    @classmethod
    def register_report(cls, name: str, report_cls: Any):
        cls._reports[name] = report_cls

    @classmethod
    def get_report(cls, name: str) -> Report:
        report_cls = cls._reports.get(name)
        if not report_cls:
            raise ValueError(f"Отчет {name} типа не найден")
        return report_cls()


ReportsData.register_report('payout', PayoutReport)

def main():
    try:
        args = parse_arguments()

        for filename in args[1]:
            try:
                with open(filename, 'r'):
                    pass
            except FileNotFoundError as e:
                print(f"Ошибка: открытия файла {filename}, файл не найден")
                return 1
            
        all_data = []
        for file in args[1]:
            try:
                file_data = read_csv(file)
                all_data.extend(file_data)
                print(f"Прочитан файл {file}")
            except Exception as e:
                print(f"Ошибка прочтения файла {file}: {e}")
                return 1
        
        try:
            report = ReportsData.get_report(args[0])
            result = report.generate(all_data)
            output = report.format_output(result)
            print(output)
        except ValueError as e:
            print(f"Ошибка: {str(e)}")
            return 1
        
        except Exception as e:
            print(f"Ошибка при генерации: {e}")
            return 1

        return 0
    
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())