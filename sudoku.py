"""
Модуль, содеражащий класс Sudoku, который вычисляет решение переданного судоку.

Ввод данных для примера:
7x8xxx3xx
xxx2x1xxx
5xxxxxxxx
x4xxxxx26
3xxx8xxxx
xxx1xxx9x
x9x6xxxx4
xxxx7x5xx
xxxxxxxxx
Где неизвестные значения могут являться любым символом, кроме цифры.
Для вычисления, используется метод calculate_result без аргументов.
"""

from time import perf_counter


class Sudoku:
    """
    Класс, использующий несколько алгоритмов поиска неизвестных значений и решающий судоку любой сложности.
    При создании нового экземпляра класса, на вход принимаются 9 строк, содержащие 9 значений.
    """

    COLUMN_LETTERS = 'abcdefghi'
    LINE_NUMBERS = '123456789'

    def __init__(self):
        self.empty_cells = [0] * 81
        self.cells = {f'{x}{y}': self.Cell(x, y, value)
                      for y in Sudoku.LINE_NUMBERS
                      for x, value in zip(Sudoku.COLUMN_LETTERS, self._validate_line(list(input())))}
        self.columns = {f'{x}': self.Column(x) for x in Sudoku.COLUMN_LETTERS}
        self.lines = {f'{y}': self.Line(y) for y in Sudoku.LINE_NUMBERS}
        self.small_squares = {number: self.SmallSquare(number) for number in range(1, 10)}

    def __str__(self):
        result = []
        count = 0
        for i, j in self.cells.items():
            count += 1
            if not count % 9:
                if count == 27 or count == 54:
                    result.append(f'{self.cells[i].value}\n\n')
                else:
                    result.append(f'{self.cells[i].value}\n')
            elif not count % 3 or not count % 6:
                result.append(f'{self.cells[i].value}    ')
            else:
                result.append(f'{self.cells[i].value}  ')
        return ''.join(result)

    @staticmethod
    def _validate_line(line):
        """ Проверка корректности введенных данных для строк. """

        if len(line) != 9:
            raise ValueError('в строке должно быть 9 значений')
        return line

    @staticmethod
    def _switch_squares(cell_key):
        """ Определение номера малого квадрата по координатам клетки. """

        if cell_key[0] in 'abc' and cell_key[1] in '123':
            return 1
        elif cell_key[0] in 'def' and cell_key[1] in '123':
            return 2
        elif cell_key[0] in 'ghi' and cell_key[1] in '123':
            return 3
        elif cell_key[0] in 'abc' and cell_key[1] in '456':
            return 4
        elif cell_key[0] in 'def' and cell_key[1] in '456':
            return 5
        elif cell_key[0] in 'ghi' and cell_key[1] in '456':
            return 6
        elif cell_key[0] in 'abc' and cell_key[1] in '789':
            return 7
        elif cell_key[0] in 'def' and cell_key[1] in '789':
            return 8
        elif cell_key[0] in 'ghi' and cell_key[1] in '789':
            return 9

    def _definition_data(self):
        """
        Начальная загрузка данных, которая происходит на старте вычесления
        результата для всех столбцов, строк и квадратов.
        """

        for cell_key in self.cells:
            cell = self.cells[cell_key]
            cell_value = cell.value
            self.columns[cell_key[0]].cells.append(cell)
            self.lines[cell_key[1]].cells.append(cell)
            switch_squares_cell = self._switch_squares(cell_key)
            self.small_squares[switch_squares_cell].cells.append(cell)
            if cell_value.isdigit():
                self.columns[cell_key[0]].values |= {cell_value}
                self.lines[cell_key[1]].values |= {cell_value}
                self.small_squares[switch_squares_cell].values |= {cell_value}
                self.empty_cells.pop()

    @staticmethod
    def _update_data(cell, column, line, small_square, empty_cells):
        """
        Обновление набора значений столбца, строки и квадрата, в которых было определено значение клетки.
        """

        cell_value = cell.value
        if cell_value in (column.values | line.values | small_square.values):
            raise ValueError(f'невозможное значение клетки {cell.x}{cell.y}: {cell_value}')
        column.values |= {cell_value}
        line.values |= {cell_value}
        small_square.values |= {cell_value}
        empty_cells.pop()

    @staticmethod
    def _get_unknown_cells(group):
        """ Возвращает все клетки с неизвестным значением в выбранной группе. """

        result = []
        for cell in group.cells:
            if not cell.value.isdigit() and len(cell.value_options) > 1:
                result.append(cell)
        return result

    @staticmethod
    def _get_max_value(group):
        """ Возвращает множество с максимальным количеством возможных значений из всех клеток в группе. """

        max_value = set()
        for cell in group:
            if len(cell.value_options) > len(max_value):
                max_value = cell.value_options
        return max_value

    @staticmethod
    def _find_common_values(square, group1, group2, group3):
        """
        Поиск общих значений малого квадрата, которые есть в двух первых группах
        (строках или столбцах малого квадрата), но нет в третьей.
        """

        set1 = set()
        set2 = set()
        set3 = set()
        for cell in square.cells:
            if group1 in [cell.x, cell.y] and cell.value_options:
                set1 |= cell.value_options
            if group2 in [cell.x, cell.y] and cell.value_options:
                set2 |= cell.value_options
            if group3 in [cell.x, cell.y]:
                if cell.value_options:
                    set3 |= cell.value_options
                else:
                    set3.add(cell.value)
        return (set1 & set2) - set3

    def _optimization_value_options(self):
        """
        Алгоритм поиска неизвестных значений, основанный на сравнении
        групп возможных значений в каждом столбце, строке и малом квадрате.
        """

        # Проверяем каждый столбец, строку и квадрат
        for data in [self.columns, self.lines, self.small_squares]:
            for key in data:
                # Находим все клетки с неизвестым значением
                unknown_cells = self._get_unknown_cells(data[key])
                # На основе этих данных проходим по всем возможным группам возможных значений,
                # основываясь на размере групп
                for group_len in range(2, len(unknown_cells)):
                    # Для каждой клетки создаем группу
                    for cell_1 in unknown_cells:
                        # Если количество возможных значений равно размеру группы, то продолжаем сравнение
                        if len(cell_1.value_options) == group_len:
                            group = [cell_1]
                            # Берем другую клетку из клеток с неизместным значением
                            for cell_2 in unknown_cells:
                                if cell_1 != cell_2 and 2 <= len(cell_2.value_options) <= group_len:
                                    # Проверяем является ли возможные значения второй клетки подмножеством первой
                                    if cell_2.value_options.issubset(cell_1.value_options):
                                        group.append(cell_2)

                            # Если размер группы равен заданному значению, то удаляем значения группы из возможных
                            # значений тех клеток, которые не входят в данную группу
                            if len(group) == group_len:
                                for cell in unknown_cells:
                                    if cell not in group:
                                        cell.value_options -= self._get_max_value(group)
                                        # Если оставщееся количество возможных значений равно единице,
                                        # значит оно равно значинию клетки
                                        if len(cell.value_options) == 1:
                                            column = self.columns[cell.x]
                                            line = self.lines[cell.y]
                                            small_square = self.small_squares[self._switch_squares(f'{cell.x}{cell.y}')]
                                            cell.value = cell.value_options.pop()
                                            self._update_data(cell, column, line, small_square, self.empty_cells)

    def _search_unique_value(self):
        """
        Дополнительный алгоритм поиска неизвестных значений, основанный на
        поиске уникального возможного значения среди всех возможных значений
        в пределах столбца, строки или малого квадрата. Если такое значение
        будет найдено, то оно и будет являтся значением клетки.
        """

        for data in [self.columns, self.lines, self.small_squares]:
            for key in data:
                data_groups = {}
                unknown_cells = self._get_unknown_cells(data[key])
                for cell in unknown_cells:
                    for option in cell.value_options:
                        try:
                            data_groups[option][0] += 1
                        except KeyError:
                            data_groups[option] = [1, cell]
                for option in data_groups:
                    if data_groups[option][0] == 1:
                        cell = data_groups[option][1]
                        cell.value = option
                        cell.value_options = set()
                        column = self.columns[cell.x]
                        line = self.lines[cell.y]
                        small_square = self.small_squares[self._switch_squares(f'{cell.x}{cell.y}')]
                        self._update_data(cell, column, line, small_square, self.empty_cells)
                        return

    def _search_intersection(self):
        """
        Дополнительный алгоритм сокращения возможных значений в клетках.

        Рассмотриваются три малых квадрата и строки (либо столбцы), их связывающие.
        Если существуют такие два квадрата, в которых пересечение с одной строкой
        (столбцом), не содержит какого-то значения либо варианта этого значения,
        которое есть в двух других пересечениях этих двух квадратов, значит в
        пересечении третьего квадрата с двумя строками (столбцами) этого
        значения быть не может.
        """

        lines_key = {1: [0, 1, 2], 2: [0, 2, 1], 3: [1, 2, 0]}
        result = None
        for count in range(1, 10):
            if not (count - 1) % 3:
                # Рассматриваем пары квдратов: 1, 2 и 1, 3 и 2, 3
                for i in range(1, 4):
                    if i == 1:
                        small_square_1 = self.small_squares[count]
                        small_square_2 = self.small_squares[count+1]
                        small_square_3 = self.small_squares[count+2]
                    elif i == 2:
                        small_square_1 = self.small_squares[count]
                        small_square_2 = self.small_squares[count+2]
                        small_square_3 = self.small_squares[count+1]
                    else:
                        small_square_1 = self.small_squares[count+1]
                        small_square_2 = self.small_squares[count+2]
                        small_square_3 = self.small_squares[count]

                    for k in range(1, 4):
                        # Достаем все номера сток из первого квадрата
                        line1 = small_square_1.lines[lines_key[k][0]]
                        line2 = small_square_1.lines[lines_key[k][1]]
                        line3 = small_square_1.lines[lines_key[k][2]]
                        # Вычисляем общие значения строк двух первых квадратов
                        values_1 = self._find_common_values(small_square_1, line1, line2, line3)
                        values_2 = self._find_common_values(small_square_2, line1, line2, line3)
                        common_values = values_1 & values_2
                        if common_values:
                            for cell in small_square_3.cells:
                                if cell.y in [line1, line2] and cell.value_options:
                                    cell_value_options = cell.value_options.copy()
                                    cell.value_options -= common_values
                                    if cell_value_options != cell.value_options:
                                        result = 1
                            if result:
                                return result

            if count in [1, 2, 3]:
                for i in range(1, 4):
                    if i == 1:
                        small_square_1 = self.small_squares[count]
                        small_square_2 = self.small_squares[count+3]
                        small_square_3 = self.small_squares[count+6]
                    elif i == 2:
                        small_square_1 = self.small_squares[count]
                        small_square_2 = self.small_squares[count+6]
                        small_square_3 = self.small_squares[count+3]
                    else:
                        small_square_1 = self.small_squares[count+3]
                        small_square_2 = self.small_squares[count+6]
                        small_square_3 = self.small_squares[count]

                    for k in range(1, 4):
                        # Достаем все номера столбцов из первого квадрата
                        column1 = small_square_1.columns[lines_key[k][0]]
                        column2 = small_square_1.columns[lines_key[k][1]]
                        column3 = small_square_1.columns[lines_key[k][2]]
                        # Вычисляем общие значения столбцов двух первых квадратов
                        values_1 = self._find_common_values(small_square_1, column1, column2, column3)
                        values_2 = self._find_common_values(small_square_2, column1, column2, column3)
                        common_values = values_1 & values_2
                        if common_values:
                            for cell in small_square_3.cells:
                                if cell.x in [column1, column2] and cell.value_options:
                                    cell_value_options = cell.value_options.copy()
                                    cell.value_options -= common_values
                                    if cell_value_options != cell.value_options:
                                        result = 1
                            if result:
                                return result

    def _calculate_unknown_cells(self):
        """
        Метод, вычисляющий неизвестные значения клеток с помощью основного алгоритма
        вычисления и дополнительных, основанных на исключении возможных значений.

        В случае полного вычесления возвращается сообщение 'end', иначе 'not completed'.
        """

        empty_cells_check = None
        while self.empty_cells:

            if empty_cells_check == len(self.empty_cells):
                self._search_unique_value()

            if empty_cells_check == len(self.empty_cells):
                result = self._search_intersection()
                if result:
                    empty_cells_check += 1

            if empty_cells_check == len(self.empty_cells):
                return 'not completed'

            empty_cells_check = len(self.empty_cells)

            for key, cell in self.cells.items():
                columns = self.columns[key[0]]
                lines = self.lines[key[1]]
                small_squares = self.small_squares[self._switch_squares(key)]
                cell.update_value_options(columns, lines, small_squares, self.empty_cells)

            self._optimization_value_options()

        return 'end'

    def _get_backup(self):
        """ Создание резервной копии всего состояния вычисляемого судоку. """

        backup = {
            'empty_cells': self.empty_cells.copy(),
            'cells': {key: cell.copy() for key, cell in self.cells.items()}
        }
        # В столбцы, строки и квадраты добавляются копии клеток, которые уже есть в бэкапе
        backup.update({'columns': {key: column.copy(backup['cells']) for key, column in self.columns.items()},
                       'lines': {key: line.copy(backup['cells']) for key, line in self.lines.items()},
                       'small_square': {key: small_square.copy(backup['cells'])
                                        for key, small_square in self.small_squares.items()}})
        return backup

    def _calculate_cell_variant(self, cell, backup, choice_value=0, cell_value_options=None, result=None):
        """
        Определение правильного варианта значения клетки из возможных значений.
        В случае ошибок всех вариантов, возвращается 'error'. Так же происходит
        запись позиции выбранного значения в 'choice_value', которая в дальнейшем
        передается в бэкап клетки.
        """

        try:
            if result == 'end':
                return {'result': result}
            elif not result or (result['result'] == 'error' and self.empty_cells):
                if result and result['result'] == 'error':
                    if choice_value > (len(cell_value_options) - 1):
                        # В случае, когда ни один вариант не подошел, передается 'error'
                        result = {'result': 'error'}
                        return result
                    backup = self._get_backup()
                    result = {'backup': backup}
                # Пытаемся угадать значение клетки из возможных вариантов
                cell.value = cell_value_options[choice_value]
                cell.value_options = set()
                column = self.columns[cell.x]
                line = self.lines[cell.y]
                small_square = self.small_squares[self._switch_squares(f'{cell.x}{cell.y}')]
                self._update_data(cell, column, line, small_square, self.empty_cells)
                if result:
                    result.update({'result': self._calculate_unknown_cells(), 'choice_value': choice_value})
                else:
                    result = {'result': self._calculate_unknown_cells(), 'choice_value': choice_value}
                return result
        except ValueError:
            # В случае ошибки, восстанавливаем предыдущее состояние клетки
            self.empty_cells = backup['empty_cells']
            self.cells = backup['cells']
            self.columns = backup['columns']
            self.lines = backup['lines']
            self.small_squares = backup['small_square']
            choice_value += 1

            return self._calculate_cell_variant(self.cells[f'{cell.x}{cell.y}'], backup, choice_value,
                                                cell_value_options, result={'result': 'error'})

    def calculate_result(self, cell_start=None, backup_dict=None):
        """
        Метод, решающий судоку. Если стандартные алгоритмы не принесли результат,
        используется метод подбора возможных значений для каждой клетки с неизвестным значением.

        При попытке решить судоку, у которого нет верного решения, выбрасывается исключение.
        """

        if not cell_start:
            backup_dict = {}
            self._definition_data()
            result = self._calculate_unknown_cells()
            self_cells = self.cells
        else:
            result = 'not completed'
            self.empty_cells = backup_dict[f'{cell_start.x}{cell_start.y}'][0]['empty_cells']
            self.cells = backup_dict[f'{cell_start.x}{cell_start.y}'][0]['cells']
            self.columns = backup_dict[f'{cell_start.x}{cell_start.y}'][0]['columns']
            self.lines = backup_dict[f'{cell_start.x}{cell_start.y}'][0]['lines']
            self.small_squares = backup_dict[f'{cell_start.x}{cell_start.y}'][0]['small_square']
            list_key = list(self.cells.keys())
            start = list_key.index(f'{cell_start.x}{cell_start.y}')
            self_cells = {key: self.cells[key] for key in list_key[start:]}
        if result == 'not completed':
            for key_cell in self_cells:
                cell = self.cells[key_cell]
                if len(cell.value_options):
                    backup = self._get_backup()
                    cell_value_options = list(backup['cells'][f'{cell.x}{cell.y}'].value_options)
                    if result == 'continue' or not cell_start:
                        result = self._calculate_cell_variant(cell, backup, cell_value_options=cell_value_options)
                    else:
                        f_key = f'{cell_start.x}{cell_start.y}'
                        if backup_dict[f_key][1] < (len(self.cells[f_key].value_options) - 1):
                            result = self._calculate_cell_variant(cell, backup,
                                                                  backup_dict[f_key][1] + 1,
                                                                  backup_dict[f_key][2])
                        else:
                            return
                    if result['result'] != 'error':
                        if result.get('backup'):
                            backup = result.get('backup')
                        backup_dict[f'{cell.x}{cell.y}'] = [backup, result['choice_value'], cell_value_options]
                    elif result['result'] == 'error':
                        first_key = next(iter(backup_dict))
                        if not cell_start or first_key == f'{cell_start.x}{cell_start.y}':
                            break
                        else:
                            backup_dict_key = [i for i in backup_dict]
                            index_cell_start = backup_dict_key.index(f'{cell_start.x}{cell_start.y}')
                            backup_dict_key = backup_dict_key[index_cell_start+1:]
                            check_choice_value = all(map(lambda x: x[1] == x[2],
                                                         [backup_dict[i] for i in backup_dict if i in backup_dict_key]))
                            if check_choice_value:
                                return
                            else:
                                break
                    if result['result'] == 'end':
                        return 'end'
                    elif result['result'] == 'not completed':
                        result = 'continue'
                        continue
        if self.empty_cells:
            backup_key = list(backup_dict.keys())[::-1]
            backup_dict_rev = {key: backup_dict[key] for key in backup_key}
            for key in backup_dict_rev:
                main_result = self.calculate_result(self.cells[key], backup_dict)
                if main_result == 'end':
                    return 'end'
            if self.empty_cells:
                raise ValueError('судоку не имеет решений')

    class Column:
        """
        Класс, содержащий все клетки одного столбца, а также известные значения.
        Реализует метод собственного копирования.
        """

        def __init__(self, x):
            self.x = x
            self.values = set()
            self.cells = []

        def copy(self, cells):
            column = Sudoku.Column(self.x)
            column.values = self.values.copy()
            column.cells = [cells[key] for key in cells
                            for cell_2 in self.cells
                            if f'{cells[key].x}{cells[key].y}' == f'{cell_2.x}{cell_2.y}']
            return column

    class Line:
        """
        Класс, содержащий все клетки одной строки, а также известные значения.
        Реализует метод собственного копирования.
        """

        def __init__(self, y):
            self.y = y
            self.values = set()
            self.cells = []

        def copy(self, cells):
            line = Sudoku.Line(self.y)
            line.values = self.values.copy()
            line.cells = [cells[key] for key in cells
                          for cell_2 in self.cells
                          if f'{cells[key].x}{cells[key].y}' == f'{cell_2.x}{cell_2.y}']
            return line

    class SmallSquare:
        """
        Класс, содержащий все клетки одного малого квадрата, все координаты
        его строк и столбцов, а также известные значения.
        Реализует метод собственного копирования.
        """

        def __init__(self, number):
            self.number = number
            self.values = set()
            self.cells = []
            self.columns = self._definition_cl('columns')
            self.lines = self._definition_cl('lines')

        def copy(self, cells):
            small_square = Sudoku.SmallSquare(self.number)
            small_square.values = self.values.copy()
            small_square.cells = [cells[key] for key in cells
                                  for cell_2 in self.cells
                                  if f'{cells[key].x}{cells[key].y}' == f'{cell_2.x}{cell_2.y}']
            small_square.columns = self.columns.copy()
            small_square.lines = self.lines.copy()
            return small_square

        def _definition_cl(self, param):
            """ Вычесление координат срок и столбцов квадрата. """

            result = {'columns': [], 'lines': []}
            if self.number in [1, 4, 7]:
                result['columns'].extend(['a', 'b', 'c'])
            elif self.number in [2, 5, 8]:
                result['columns'].extend(['d', 'e', 'f'])
            elif self.number in [3, 6, 9]:
                result['columns'].extend(['g', 'h', 'i'])

            if self.number in [1, 2, 3]:
                result['lines'].extend(['1', '2', '3'])
            elif self.number in [4, 5, 6]:
                result['lines'].extend(['4', '5', '6'])
            elif self.number in [7, 8, 9]:
                result['lines'].extend(['7', '8', '9'])

            if param == 'columns':
                return result['columns']
            elif param == 'lines':
                return result['lines']

    class Cell:
        """
        Класс клетки, создержащий ее координаты, значение и возможные значения этой клетки.
        Реализует метод копирования и метод вычисления возможных значений.
        """

        def __init__(self, x, y, value):
            self.x = x
            self.y = y
            self.value = value
            self.value_options = set() if self.value.isdigit() else {str(i) for i in range(1, 10)}

        def copy(self):
            cell = Sudoku.Cell(self.x, self.y, self.value)
            cell.value_options = self.value_options.copy()
            return cell

        def update_value_options(self, column, line, small_square, empty_cells):
            """
            Вычисляет возможные значения клетки. В случае, если возможное значение одно,
            устанавливет его в значение этой клетки и производит обновление данных судоку.
            """

            self.value_options -= column.values
            self.value_options -= line.values
            self.value_options -= small_square.values
            if not self.value_options and not self.value.isdigit():
                raise ValueError
            if not self.value.isdigit() and len(self.value_options) == 1:
                self.value = self.value_options.pop()
                Sudoku._update_data(self, column, line, small_square, empty_cells)


if __name__ == '__main__':
    a = Sudoku()
    t1 = perf_counter()
    a.calculate_result()
    print(a)
    print('Lead time:', perf_counter() - t1)
